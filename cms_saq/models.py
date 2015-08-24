from django.db import models
from django.db.models import Max, Sum

from cms.models import CMSPlugin, Page, Placeholder
from cms.models.fields import PageField
from taggit.managers import TaggableManager

from djangocms_text_ckeditor.models import AbstractText


class QuestionnaireText(AbstractText):
    """ Text plugin which, when rendered is translated
        using django translations.  Also provides
        means of making text dependent on SAQ answers.
    """
    depends_on_answer = models.ForeignKey(
        'cms_saq.Answer', null=True, blank=True, related_name='trigger_text')

    def copy_relations(self, oldinstance):
        self.depends_on_answer = oldinstance.depends_on_answer


class Answer(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    help_text = models.TextField(blank=True, null=True)
    score = models.IntegerField(default=0)
    order = models.IntegerField(default=0)
    question = models.ForeignKey('cms_saq.Question', related_name="answers")

    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ('question', 'order', 'slug')
        unique_together = (('question', 'slug'),)

    def __unicode__(self):
        return u"%s: %s" % (self.question.slug, self.title)


class GroupedAnswer(Answer):
    group = models.CharField(max_length=255)

    class Meta:
        ordering = ('group', 'order', 'slug')


class Question(CMSPlugin):
    QUESTION_TYPES = [
        ('S', 'Single-choice question'),
        ('M', 'Multi-choice question'),
        ('F', 'Free-text question'),
    ]

    slug = models.SlugField(
        help_text="A slug for identifying answers to this specific question "
        "(allows multiple only for multiple languages)")
    tags = TaggableManager(blank=True)
    label = models.CharField(max_length=512, blank=True)
    help_text = models.CharField(max_length=512, blank=True)
    question_type = models.CharField(max_length=1, choices=QUESTION_TYPES)
    optional = models.BooleanField(
        default=False,
        help_text="Only applies to free text questions",
    )

    depends_on_answer = models.ForeignKey(
        Answer, null=True, blank=True, related_name='trigger_questions')

    def copy_relations(self, oldinstance):
        for answer in oldinstance.answers.all():
            answer.pk = None
            answer.question = self
            answer.save()

        self.depends_on_answer = oldinstance.depends_on_answer

    @staticmethod
    def all_in_tree(page):
        root = page.get_root()
        # Remember that there might be questions on the root page as well!
        tree = root.get_descendants() | Page.objects.filter(id=root.id)
        placeholders = Placeholder.objects.filter(page__in=tree)
        return Question.objects.filter(placeholder__in=placeholders)

    @staticmethod
    def all_in_page(page):
        placeholders = Placeholder.objects.filter(page=page)
        return Question.objects.filter(placeholder__in=placeholders)

    def score(self, answers):
        if self.question_type == 'F':
            return 0
        elif self.question_type == 'S':
            return self.answers.get(slug=answers).score
        elif self.question_type == 'M':
            answers_list = answers.split(',')
            return sum([self.answers.get(slug=a).score for a in answers_list])

    @property
    def max_score(self):
        if not hasattr(self, '_max_score'):
            if self.question_type == "S":
                self._max_score = self.answers.aggregate(
                    Max('score'))['score__max']
            elif self.question_type == "M":
                self._max_score = self.answers.aggregate(
                    Sum('score'))['score__sum']
            else:
                self._max_score = None  # don't score free-text answers
        return self._max_score

    def percent_score_for_user(self, user):
        if self.max_score:
            try:
                score = Submission.objects.get(
                    question=self.slug,
                    user=user,
                ).score
            except Submission.DoesNotExist:
                return 0
            return 100.0 * score / self.max_score
        else:
            return None

    def __unicode__(self):
        return self.slug


class SubmissionSet(models.Model):
    """ A set of submissions stored and associated with a particular user to
        provide a mechanism through which a single user can provide repeated
        sets of answers to the same questionnaire.
    """
    slug = models.SlugField(blank=True)
    tag = models.SlugField(blank=True)
    user = models.ForeignKey('auth.User', related_name='saq_submissions_sets')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class Submission(models.Model):
    question = models.SlugField()
    answer = models.TextField(blank=True)
    score = models.IntegerField()
    user = models.ForeignKey('auth.User', related_name='saq_submissions')

    submission_set = models.ForeignKey(
        SubmissionSet, related_name='submissions', null=True)

    class Meta:
        ordering = ('submission_set', 'user', 'question')
        unique_together = ('question', 'user', 'submission_set')

    def answer_list(self):
        return self.answer.split(",")

    def __unicode__(self):
        return u"%s answer to %s (%s)" % (
            self.user, self.question, self.submission_set.slug
            if self.submission_set else "default")


class FormNav(CMSPlugin):
    next_page = PageField(blank=True, null=True, related_name="formnav_nexts")
    next_page_label = models.CharField(max_length=255, blank=True, null=True)
    prev_page = PageField(blank=True, null=True, related_name="formnav_prevs")
    prev_page_label = models.CharField(max_length=255, blank=True, null=True)
    end_page = PageField(blank=True, null=True, related_name="formnav_ends")
    end_page_label = models.CharField(max_length=255, blank=True, null=True)
    end_page_condition_question = models.ForeignKey(
        Question, null=True, blank=True)

    submission_set_tag = models.CharField(
        max_length=255, blank=True, null=True)

    def copy_relations(self, old):
        self.end_page_condition_question = old.end_page_condition_question


class SubmissionSetReview(CMSPlugin):
    """ Plugin to list and review questionnaire submission sets
    """

    submission_set_tag = models.CharField(
        max_length=255, blank=True, null=True)

    count_optional = models.BooleanField(default=False)

    label = models.CharField(max_length=255)

    def sets_for_user(self, user):
        """ Return available submission sets for the given user
        """
        _sets = SubmissionSet.objects.filter(
            user=user,
            slug__startswith=self.submission_set_tag
        )
        return _sets

    @property
    def num_questions(self):
        questions = Question.all_in_tree(self.page)

        if not self.count_optional:
            questions = questions.filter(optional=False)

        return questions.count()


class SectionedScoring(CMSPlugin):
    def scores_for_user(self, user):
        scores = [
            [s.label, s.score_for_user(user)] for s in self.sections.all()]
        overall = sum([s[1] for s in scores]) / len(scores)
        return [scores, overall]

    def copy_relations(self, oldinstance):
        self.sections = oldinstance.sections.all()


class ScoreSection(models.Model):
    group = models.ForeignKey(
        'cms_saq.SectionedScoring', related_name='sections')
    label = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    order = models.IntegerField()

    class Meta:
        ordering = ('order', 'label')

    def score_for_user(self, user):
        return aggregate_score_for_user_by_tags(user, [self.tag])


class ProgressBar(CMSPlugin):
    count_optional = models.BooleanField(default=False)

    def progress_for_user(self, user):
        subs = Submission.objects.filter(
            user=user,
            submission_set=None
        ).values_list('question', flat=True)
        questions = Question.all_in_tree(self.page)

        if not self.count_optional:
            questions = questions.filter(optional=False)

        answered = questions.filter(slug__in=subs)

        return (answered.count(), questions.count())


class BulkAnswer(CMSPlugin):
    """Answer all questions on the current page with a given value."""
    answer_value = models.CharField(max_length=255)
    label = models.CharField(
        max_length=255, help_text="e.g.: 'mark all as not applicable'",
    )


def aggregate_score_for_user_by_questions(user, questions):
    scores = []
    for question in questions:
        score = question.percent_score_for_user(user)
        if score is not None:
            scores.append(score)
    if len(scores):
        return sum(scores) / len(scores)
    else:
        return 0


def aggregate_score_for_user_by_tags(user, tags):
    questions = Question.objects.filter(tags__name__in=tags).distinct()
    scores = []
    for question in questions:
        score = question.percent_score_for_user(user)
        if score is not None:
            scores.append(score)
    if len(scores):
        return sum(scores) / len(scores)
    else:
        return 0
