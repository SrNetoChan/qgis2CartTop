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
    o = recartObject('ConstruLinear.json')
    print(o.name)
    print(o.long_name)
    print(o.theme)
    if o.is3d:
        print("It's a 3D")
    print(o.attributes())
    print(o.domains())

if __name__ == "__main__":
    main()
