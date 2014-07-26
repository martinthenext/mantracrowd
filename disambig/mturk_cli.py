from mturk import *
from django.conf import settings

connection = MTurkConnection(aws_access_key_id=settings.MTURK_ACCESS_KEY, aws_secret_access_key=settings.MTURK_SECRET_KEY,
 host=MTURK_HOST)

print "Welcome to MTURK CLI, account balance is %s" % connection.get_account_balance()

# get all hits for the requester, and all their assignments
def list_assignments():
  for hit in connection.get_all_hits():
    hit_assignments = connection.get_assignments(hit.HITId)
    if hit.expired:
      print "HIT %s - expired - %s ASSIGNMENTS" % (hit.HITId, len(hit_assignments))
    else:
      print "HIT %s - %s ASSIGNMENTS" % (hit.HITId, len(hit_assignments))
    
    print "URL %s" % get_hit_url(hit)
    # list all assignments for that hit
    for assignment in connection.get_assignments(hit.HITId):
      print "-- %s WORKER %s" % (assignment.AssignmentId, assignment.WorkerId)  

# All assignments will be approved as a result of this action
def disable_all_hits():
  for hit in connection.get_all_hits():
    connection.disable_hit(hit.HITId)
