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

class recartObject():
    def __init__(self, path):
        with open(path) as f:
            self.raw_data = json.load(f)
        self.name = self.raw_data['objecto']['objeto']
        self.long_name = self.raw_data['objecto']['Característica geográfica']
        self.theme = self.raw_data['objecto']['Tema']

    def is3d(self):
        return self.raw_data['objecto']['Dim.'] == '3D'

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
        return not self.d1=='x' or self.multiplicity=='[0..1]'

def convert(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def main():
    # Get RECART objects folder absolute path
    objects_path = os.path.abspath(os.path.join(os.path.dirname( __file__ )
        , '..'
        , 'RECART'
        , 'objectos'))

    # Find all JSON files
    filepaths = []
    for root, dirnames, filenames in os.walk(objects_path):
        for filename in fnmatch.filter(filenames, '*.json'):
            if filename != 'relacoes.json':
                filepaths.append(os.path.join(root, filename))

    # Create dictionary with all code domains
    listas_codigos = {}
    for file in filepaths:
        o = recartObject(file)
        listas_codigos.update(o.domains())
    
    # Save all code domains into a json file
    listas_codigos_path = os.path.abspath(os.path.join(os.path.dirname( __file__ )
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
