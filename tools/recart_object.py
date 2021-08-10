# -*- coding: utf-8 -*-

#-----------------------------------------------------------
# Copyright (C) 2019 Alexandre Neto
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 3
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import json
import re
import os, fnmatch
from jinja2 import Template, Environment, PackageLoader, select_autoescape

class recartObject():
    def __init__(self, path):
        with open(path) as f:
            self.raw_data = json.load(f)
        self.name = self.raw_data['objecto']['objeto']
        self.long_name = self.raw_data['objecto']['Característica geográfica']
        self.theme = self.raw_data['objecto']['Tema']

    def dimension(self):
        return self.raw_data['objecto']['Dim.']
    
    def geometry(self):
        attributes = self.raw_data['objecto']['Atributos']
        geometria = None
        vector_type = None

        p_vector_types = dict (
            linha = 'QgsProcessing.TypeVectorLine',
            ponto = 'QgsProcessing.TypeVectorPoint',
            polígono = 'QgsProcessing.TypeVectorPolygon',
            multipolígono = 'QgsProcessing.TypeVectorPolygon')

        for attribute in attributes:
            if attribute['Atributo'] == 'geometria':
                geometria = attribute['Tipo']
                geometria = geometria.replace('Geometria (','')
                geometria = geometria.replace(')','')
                geometria = geometria.split('; ')
                vector_type = [p_vector_types[g] for g in geometria]
                geometria = ' ou '.join(geometria)
                vector_type = ', '.join(vector_type)
        return geometria, vector_type

    def attributes(self):
        attributes = self.raw_data['objecto']['Atributos']
        list_attributes = []
        for attribute in attributes:
            list_attributes.append(recartAttribute(attribute))
        return list_attributes

    def domains(self):
        domains = self.raw_data['objecto']['listas de códigos']
        list_domains = {}
        for domain in domains:
            valores_dict = {}
            for valor in domain['valores']:
                valores_dict[valor['Descrição']] = valor['Valores']
            list_domains[domain['nome']] = valores_dict
        return list_domains

class recartAttribute():
    def __init__(self, dict):
        self.name = dict['Atributo']
        self.type = dict['Tipo']
        self.definition = dict['Definição']
        self.multiplicity = dict['Multip.']
        self.d1 = dict['D1']
        self.d2 = dict['D2']

    def isMandatory(self):
        return self.d1=='x' and self.multiplicity == '1'

def convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def abbreviation(name):
    words = convert(name).split('_')
    return ''.join([w[0] for w in words])

def toProcessingParameter(attribute):
    if attribute.name in ('identificador','geometria','inicioObjeto','fimObjeto'):
        return ''

    code = ''
    cod_values = ''
    number_type = ''

    print(attribute.type)

    if attribute.type == 'Lista de códigos':
        code += f"self.cod_keys, self.cod_values = get_lista_codigos('{attribute.name}')\n\n"
        parameter_type = "QgsProcessingParameterEnum"
        cod_values = '         self.cod_values,\n'
    elif attribute.type in ('Texto','Data','DataTempo'):
        parameter_type = "QgsProcessingParameterString"
    elif attribute.type == 'Booleano':
        parameter_type = "QgsProcessingParameterBoolean"
    elif attribute.type == 'Real':
        parameter_type = "QgsProcessingParameterNumber"
        number_type = '         1,\n'
    elif attribute.type == 'Inteiro':
        parameter_type = "QgsProcessingParameterNumber"
        number_type = '         0,\n'

    code += "self.addParameter(\n"
    code += f"    {parameter_type}(\n"
    code += f"         self.{convert(attribute.name).upper()},\n" \
            f"         self.tr('{attribute.name}'),\n" \
            f"{cod_values}" \
            f"{number_type}"
    code += f"         defaultValue=0,\n" \
            f"         optional={attribute.isMandatory()},\n" \
            f"    )\n" \
            f")\n"

    return code

def main():
    # Get RECART objects folder absolute path
    script_path = os.path.dirname( __file__ )
    objects_path = os.path.abspath(os.path.join(script_path
        , '..'
        , 'RECART'
        , 'objectos'))

    # Find all JSON files
    filepaths = []
    for root, dirnames, filenames in os.walk(objects_path):
        for filename in fnmatch.filter(filenames, '*.json'):
            if filename != 'relacoes.json':
                filepaths.append(os.path.join(root, filename))

    temas_dict = {
        '01':'UNIDADES ADMINISTRATIVAS',
        '02':'TOPONÍMIA',
        '03':'ALTIMETRIA',
        '04':'HIDROGRAFIA',
        '05':'TRANSPORTES',
        '06':'CONSTRUÇÕES',
        '07':'OCUPAÇÃO DO SOLO',
        '08':'INFRAESTRUTURAS E SERVIÇOS DE INTERESSE PÚBLICO',
        '09':'MOBILIÁRIO URBANO E SINALIZAÇÃO',
        '11':'AUXILIAR'
        }


    stub_file_path = os.path.join(script_path, 'processing_tool_stub.pys')

    with open(stub_file_path) as f:
        code_template = Template(f.read())

    # Create dictionary with all code domains
    listas_codigos = {}
    for file in filepaths:
        o = recartObject(file)
        listas_codigos.update(o.domains())

        values = list(temas_dict.values())
        if o.theme.upper() in values:
            idx = values.index(o.theme.upper())
            numero_tema = list(temas_dict.keys())[idx]
        else:
            numero_tema = 'XX'
        parameters = []
        for a in o.attributes():
            print(a.name)
            print(a.type)
            print(a.isMandatory())
            if a.isMandatory() and not a.name in ('identificador','geometria','inicioObjeto','fimObjeto'):
                number_type = None

                if a.type == 'Lista de códigos':
                    parameter_type = "QgsProcessingParameterEnum"
                    refactor_type = '10'
                elif a.type == 'Texto':
                    parameter_type = "QgsProcessingParameterString"
                    refactor_type = '10'                    
                elif a.type == 'Data':
                    parameter_type = "QgsProcessingParameterString"
                    refactor_type = '14'
                elif a.type == 'DataTempo':
                    parameter_type = "QgsProcessingParameterString"
                    refactor_type = '16'                  
                elif a.type == 'Booleano':
                    parameter_type = "QgsProcessingParameterBoolean"
                    refactor_type = '1'
                elif a.type == 'Real':
                    parameter_type = "QgsProcessingParameterNumber"
                    number_type = '1'
                    refactor_type = '6'
                elif a.type == 'Inteiro':
                    parameter_type = "QgsProcessingParameterNumber"
                    number_type = '0'
                    refactor_type = '2'
                
                an_attribute = dict(name=a.name,
                                    display_name = convert(a.name).replace('_',' ').title(),
                                    abv = abbreviation(a.name),
                                    constant=convert(a.name).upper(),
                                    type = a.type,
                                    parameter_type = parameter_type,
                                    number_type = number_type,
                                    refactor_type = refactor_type
                                    )
                parameters.append(an_attribute)
            
            geometria, vector_type = o.geometry()

        tool_code = code_template.render(
            nome_ferramenta = o.name,
            table = convert(o.name),
            display_name = o.long_name,
            tema = o.theme.title(),
            numero_tema = numero_tema,
            geometria = geometria,
            vector_type = vector_type,
            dimensao = o.dimension(),
            parameters = parameters
            )
        print(tool_code)

        output_file_path = os.path.abspath(os.path.join(script_path
        , '..'
        , 'qgis2CartTop'
        , 'processing_provider'
        , 'extras'
        , 'stubs'
        , f'exportar_{convert(o.name)}.py'))

        with open(output_file_path, "w") as f:
            f.write(tool_code)
    
    # Save all code domains into a json file
    listas_codigos_path = os.path.abspath(os.path.join(script_path
        , '..'
        , 'qgis2CartTop'
        , 'processing_provider'
        , 'extras'
        , 'listas_codigos.json'))

    # note that output.json must already exist at this point
    with open(listas_codigos_path, 'w', encoding='utf8') as f:
        # this would place the entire output on one line
        # use json.dump(lista_items, f, indent=4) to "pretty-print" with four spaces per indent
        json.dump(listas_codigos, f, indent = 4, ensure_ascii=False)

if __name__ == "__main__":
    main()
