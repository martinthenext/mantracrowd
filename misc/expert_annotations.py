""" Takes raw expert annotations file and adds information from the 
    database for machine processing (ie creating Annotation objects, see mantracrowd/data.py)
"""

from disambig.models import *

import sys
import codecs

import numpy as np

sys.stdout = codecs.getwriter('utf-8')(sys.__stdout__)

with codecs.open('misc/expert_annotations_raw.csv', 'r', 'utf-8') as f:
  with codecs.open('misc/expert_annotations_machine.tsv', 'w', 'utf-8') as out:  
    out.write(u"""len\toffset\tgroups\ttext\tunit_text\texpert_annotation\n""")

    for line in f:
      row = line.strip().split(u";")
      data_id = row[0]
      expert_vote = unicode(row[-2]).upper()
      question = DisambigPollData.objects.get(id=data_id)
      majorty_vote = unicode(question.get_majority_vote()).upper()
      agreed = (majorty_vote == expert_vote)
      out.write(u"\t".join([
        str(question.length),
        str(question.offset),
        question.groups,
        question.text,
        question.unit_text,
        expert_vote,
      ]) + "\n")
