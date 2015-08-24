"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import json

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client, RequestFactory
from django.template import Template, RequestContext

from cms_saq.models import Submission, Question


class SubmissionTest(TestCase):
    fixtures = ['submission_test']

    def setUp(self):
        self.client = Client()

    def test_submit_one_singlechoiceanswer(self):
        """Send one SingleChoiceAnswer submission to the submit view"""
        r = self.client.post(reverse('cms_saq_submit'), {'favourite-colour': 'red'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(1, Submission.objects.all().count())
        Submission.objects.get(question='favourite-colour', answer='red', score=10)

    def test_submit_two_singlechoiceanswers(self):
        """Send two SingleChoiceAnswer submissions to the submit view"""
        r = self.client.post(reverse('cms_saq_submit'), {'favourite-colour': 'red', 'favourite-sport': 'football'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(2, Submission.objects.all().count())
        s1 = Submission.objects.get(question='favourite-colour', answer='red', score=10)
        s2 = Submission.objects.get(question='favourite-sport', answer='football', score=40)
        self.assertEqual(s1.user, s2.user)

    def test_submit_singlechoiceanswer_update(self):
        """Send one SingleChoiceAnswer submission to the submit view, then update it"""
        r = self.client.post(reverse('cms_saq_submit'), {'favourite-colour': 'red'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(1, Submission.objects.all().count())
        s1 = Submission.objects.get(question='favourite-colour', answer='red', score=10)
        r = self.client.post(reverse('cms_saq_submit'), {'favourite-colour': 'green'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(1, Submission.objects.all().count())
        s2 = Submission.objects.get(question='favourite-colour', answer='green', score=20)
        self.assertEqual(s1.user, s2.user)

    def test_submit_one_multichoiceanswer_update(self):
        """Send one MultiChoiceAnswer submission to the submit view."""
        r = self.client.post(reverse('cms_saq_submit'), {'sports-you-play': 'football,rugby'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(1, Submission.objects.all().count())
        Submission.objects.get(question='sports-you-play', answer='football,rugby', score=150)

    def test_submit_freetextanswer(self):
        """Ensure free-text answers don't get parsed/validated as choices."""
        r = self.client.post(reverse('cms_saq_submit'), {'favourite-team': 'Bath RFC'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(1, Submission.objects.all().count())
        Submission.objects.get(question='favourite-team', answer='Bath RFC', score=0)


class ScoresTest(TestCase):
    fixtures = ['scores_test']

    def setUp(self):
        self.client = Client()
        self.questions = ['favourite-colour', 'favourite-sport', 'sports-you-play']

    def test_complete_scores(self):
        """Test the 'scores' view."""
        self.client.login(username="uncle_bill", password="password")
        resp = self.client.get(reverse('cms_saq_scores'), {'q': self.questions})
        self.assertEqual(resp.status_code, 200, resp.content)
        data = json.loads(resp.content)
        self.assertEqual(data, {
            'questions': self.questions,
            'complete': True,
            'submissions': {
                'favourite-colour': {
                    'answer': 'red',
                    'score': 10
                },
                'favourite-sport': {
                    'answer': 'football',
                    'score': 40
                },
                'sports-you-play': {
                    'answer': 'football,rugby,cricket',
                    'score': 350
                }
            }
        })

    def test_incomplete_scores(self):
        """Test the 'scores' view where not all questions have been answered
        """
        self.client.login(username='auntie_rach', password='password')
        resp = self.client.get(reverse('cms_saq_scores'), {'q': self.questions})
        self.assertEqual(resp.status_code, 200, resp.content)
        data = json.loads(resp.content)
        self.assertEqual(data, {
            'questions': self.questions,
            'complete': False,
            'submissions': {
                'favourite-colour': {
                    'answer': 'blue',
                    'score': 30
                },
                'favourite-sport': {
                    'answer': 'cricket',
                    'score': 60
                },
            }
        })


class TemplateTagsTest(TestCase):
    fixtures = ['scores_test', 'submission_test']

    def setUp(self):
        self.factory = RequestFactory()

    def _request_for_user(self, username):
        request = self.factory.get('/foobar')
        request.user = User.objects.get(username=username)
        return request

    def test_saq_raw_answer(self):
        request = self._request_for_user('auntie_rach')
        # test for an existing answer
        template = Template("{% load saq_tags %}{% saq_raw_answer \"favourite-team\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, 'McLaren')
        # test for a non-existent answer
        template = Template("{% load saq_tags %}{% saq_raw_answer \"favourite-ice-cream\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, '')

    def test_saq_nice_answer(self):
        request = self._request_for_user('auntie_rach')
        # test for an existing answer
        template = Template("{% load saq_tags %}{% saq_nice_answer \"favourite-sport\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, 'Cricket')
        # test for a non-existent answer
        template = Template("{% load saq_tags %}{% saq_nice_answer \"favourite-ice-cream\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, '')

    def test_saq_percent_score(self):
        request = self._request_for_user('uncle_bill')
        template = Template("{% load saq_tags %}{% saq_percent_score \"favourite-colour\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, '33')
        request = self._request_for_user('auntie_rach')
        template = Template("{% load saq_tags %}{% saq_percent_score \"favourite-colour\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, '100')
        template = Template("{% load saq_tags %}{% saq_percent_score \"favourite-ice-cream\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, '0')

    def test_saq_aggregate_percent_score_by_tags(self):
        # setup tags, 'cos fixtures suck for tags
        Question.objects.get(slug='favourite-colour').tags.add('favourites')
        Question.objects.get(slug='favourite-sport').tags.add('favourites', 'sports')
        Question.objects.get(slug='sports-you-play').tags.add('sports')
        request = self._request_for_user('uncle_bill')
        template = Template("{% load saq_tags %}{% saq_aggregate_percent_score_by_tags \"favourites\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, '50')
        request = self._request_for_user('auntie_rach')
        template = Template("{% load saq_tags %}{% saq_aggregate_percent_score_by_tags \"favourites\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, '100')
        request = self._request_for_user('uncle_bill')
        template = Template("{% load saq_tags %}{% saq_aggregate_percent_score_by_tags \"favourites,sports\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, '67')
        request = self._request_for_user('auntie_rach')
        template = Template("{% load saq_tags %}{% saq_aggregate_percent_score_by_tags \"favourites,sports\" %}")
        out = template.render(RequestContext(request))
        self.assertEqual(out, '67')

