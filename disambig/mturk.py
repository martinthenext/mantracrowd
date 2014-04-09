''' KNOWLEDGE

One turker can only do one assignment per HIT, so if we want turkers to do assignments several
times, gotta post several HITs

Assignments do get automatically accepted once you disable the HIT 

'''

from django.conf import settings

#MTURK_HOST = 'mechanicalturk.amazonaws.com'
MTURK_HOST = settings.MTURK_SANDBOX_HOST

from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price

def get_hit_url(hit):
  return """https://workersandbox.mturk.com/mturk/preview?groupId=""" + hit.HITTypeId
  #return """https://mturk.com/mturk/preview?groupId=""" + hit.HITTypeId

def create_disambig_hit():
  connection = MTurkConnection(aws_access_key_id=settings.MTURK_ACCESS_KEY, aws_secret_access_key=settings.MTURK_SECRET_KEY,
   host=MTURK_HOST)

  question = ExternalQuestion('https://kitt.cl.uzh.ch/kitt/mantracrowd-static/disambiguation.html', 500)
  result = connection.create_hit(
    question=question, 
    title='Disambiguation survey',
    description='Answer questions about word meanings',
    reward=Price(0.30),
    keywords='language, English, text, linguistics',
    max_assignments=3,
    # 3 days
    lifetime=3*24*60*60, 
    annotation="Disambiguation survey"
    )

  return result[0]

def create_hit_get_url():
  hit = create_disambig_hit()
  return get_hit_url(hit)

def finalize_assignment(assignment_id, approve=True):
  connection = MTurkConnection(aws_access_key_id=MTURK_ACCESS_KEY, aws_secret_access_key=MTURK_SECRET_KEY,
   host=MTURK_HOST)

  if approve:
    connection.approve_assignment(assignment_id)
  else:
    connection.reject_assignment(assignment_id)

def get_assignment_list(hit_id):
  connection = MTurkConnection(aws_access_key_id=MTURK_ACCESS_KEY, aws_secret_access_key=MTURK_SECRET_KEY,
   host=MTURK_HOST)
  # Valid Values: Submitted | Approved | Rejected
  return connection.get_assignments(hit_id)

def get_all_hit_stats():
  connection = MTurkConnection(aws_access_key_id=MTURK_ACCESS_KEY, aws_secret_access_key=MTURK_SECRET_KEY,
   host=MTURK_HOST)
  for row in [(hit.HITId, hit.expired) for hit in connection.get_all_hits()]:
    print "%s - %s" % row