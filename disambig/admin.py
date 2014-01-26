from django.contrib import admin
from models import DisambigPollData, UserState, UserAnswer, Hit, TestQuestion, TestQuestionUserAnswer

admin.site.register(DisambigPollData)
admin.site.register(UserState)
admin.site.register(UserAnswer)
admin.site.register(Hit)
admin.site.register(TestQuestion)
admin.site.register(TestQuestionUserAnswer)