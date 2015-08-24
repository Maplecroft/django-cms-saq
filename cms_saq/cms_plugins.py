import itertools
import operator

from django.contrib import admin
from django.utils.translation import ugettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from cms_saq.models import Question, Answer, GroupedAnswer, Submission, \
    FormNav, ProgressBar, SectionedScoring, ScoreSection, BulkAnswer, \
    QuestionnaireText, SubmissionSetReview


from djangocms_text_ckeditor.cms_plugins import TextPlugin
from djangocms_text_ckeditor.models import Text

from bs4 import BeautifulSoup


class TranslatedTextPlugin(TextPlugin):
    """ Text plugin that pushes every text string through i18n translations
        when rendered.
    """

    model = Text
    name = "TranslatedText"
    render_template = "cms_saq/translated_text.html"

    def render(self, context, instance, placeholder):
        """ Over-ride render to use bs4 to break up strings in HTML
        """
        soup = BeautifulSoup(instance.body)
        for string in list(soup.strings):
            string.replace_with(_(unicode(string)))
        context['translated'] = unicode(soup)
        return context


class QuestionnaireTextPlugin(TranslatedTextPlugin):
    """ Questionnaire text dependent on answers
    """
    model = QuestionnaireText
    render_template = "cms_saq/questionnaire_text.html"
    module = "SAQ"
    name = "QuestionnaireText"

    def render(self, context, instance, placeholder):
        context = super(QuestionnaireTextPlugin, self).render(
            context, instance, placeholder,
        )
        user = context['request'].user

        triggered = True
        depends_on = None
        submission_set = None

        if instance.depends_on_answer:
            depends_on = instance.depends_on_answer.pk
            try:
                Submission.objects.get(
                    user=user,
                    question=instance.depends_on_answer.question.slug,
                    answer=instance.depends_on_answer.slug,
                    submission_set=submission_set,
                )
                triggered = True
            except:
                triggered = False

        extra = {
            'triggered': triggered,
            'depends_on': depends_on,
        }

        context.update(extra)
        return context


class AnswerAdmin(admin.StackedInline):
    model = Answer
    extra = 0
    verbose_name = "answer"
    prepopulated_fields = {"slug": ("title",)}


class NoHelpTextAnswerAdmin(AnswerAdmin):
    exclude = ('help_text',)


class NoHelpTextGroupedAnswerAdmin(NoHelpTextAnswerAdmin):
    model = GroupedAnswer


class QuestionPlugin(CMSPluginBase):
    model = Question
    module = "SAQ"
    inlines = [AnswerAdmin]
    exclude = ('question_type',)

    def render(self, context, instance, placeholder):
        user = context['request'].user

        submission_set = None

        triggered = True
        depends_on = None
        if instance.depends_on_answer:
            depends_on = instance.depends_on_answer.pk
            try:
                Submission.objects.get(
                    user=user,
                    question=instance.depends_on_answer.question.slug,
                    answer=instance.depends_on_answer.slug,
                    submission_set=submission_set,
                )
                triggered = True
            except:
                triggered = False

        extra = {
            'question': instance,
            'answers': instance.answers.all(),
            'triggered': triggered,
            'depends_on': depends_on,
        }

        if user.is_authenticated():
            try:
                extra['submission'] = Submission.objects.get(
                    user=user,
                    question=instance.slug,
                    submission_set=submission_set,
                )
            except Submission.DoesNotExist:
                pass

        context.update(extra)
        return context

    def save_model(self, request, obj, form, change):
        obj.question_type = self.question_type
        super(QuestionPlugin, self).save_model(request, obj, form, change)


class SessionDefinition(QuestionPlugin):
    name = "Session Definition"
    render_template = "cms_saq/single_choice_question.html"
    question_type = "S"
    exclude = ('question_type', 'help_text')


class SingleChoiceQuestionPlugin(QuestionPlugin):
    name = "Single Choice Question"
    render_template = "cms_saq/single_choice_question.html"
    question_type = "S"
    exclude = ('question_type', 'help_text')


class MultiChoiceQuestionPlugin(QuestionPlugin):
    name = "Multi Choice Question"
    render_template = "cms_saq/multi_choice_question.html"
    question_type = "M"
    exclude = ('question_type', 'help_text')


class DropDownQuestionPlugin(QuestionPlugin):
    name = "Drop-down Question"
    render_template = "cms_saq/drop_down_question.html"
    inlines = [NoHelpTextAnswerAdmin]
    question_type = "S"


class GroupedDropDownQuestionPlugin(QuestionPlugin):
    name = "Grouped Drop-down Question"
    render_template = "cms_saq/drop_down_question.html"
    inlines = [NoHelpTextGroupedAnswerAdmin]
    question_type = "S"

    def render(self, context, instance, placeholder):
        new_ctx = super(GroupedDropDownQuestionPlugin, self).render(
            context, instance, placeholder,
        )
        answers = list(
            GroupedAnswer.objects.filter(question__slug=instance.slug)
        )
        grouped_answers = itertools.groupby(
            answers, operator.attrgetter('group'),
        )
        grouped_answers = [
            [key, list(group)] for key, group in grouped_answers
        ]
        new_ctx.update({'grouped_answers': grouped_answers})
        return new_ctx


class FreeTextQuestionPlugin(QuestionPlugin):
    name = "Free Text Question"
    render_template = "cms_saq/free_text_question.html"
    inlines = []
    question_type = "F"


class FreeNumberQuestionPlugin(FreeTextQuestionPlugin):
    name = "Free Number Question"

    def render(self, context, instance, placeholder):
        context = super(FreeNumberQuestionPlugin, self).render(
            context, instance, placeholder,
        )
        context['numeric'] = True
        return context


class FormNavPlugin(CMSPluginBase):
    model = FormNav
    name = "Back / Next Buttons"
    module = "SAQ"
    render_template = "cms_saq/form_nav.html"

    def render(self, context, instance, placeholder):
        met_end_condition = False

        if instance.end_page_condition_question:
            end_condition_slug = instance.end_page_condition_question.slug
            met_end_condition = (Submission.objects
                .filter(user=context['user'], question=end_condition_slug)
                .count()) > 0
        context.update({
            'instance': instance,
            'met_end_condition': met_end_condition,
        })
        return context


class ScoreSectionAdmin(admin.TabularInline):
    model = ScoreSection
    extra = 0
    verbose_name = "section"


class SectionedScoringPlugin(CMSPluginBase):
    model = SectionedScoring
    name = "Sectioned Scoring"
    module = "SAQ"
    render_template = "cms_saq/sectioned_scoring.html"
    inlines = [ScoreSectionAdmin]

    def render(self, context, instance, placeholder):
        scores, overall = instance.scores_for_user(context['request'].user)
        context.update({
            'scores': scores,
            'overall': overall
        })
        return context


class ProgressBarPlugin(CMSPluginBase):
    model = ProgressBar
    name = "Progress Bar"
    module = "SAQ"
    render_template = "cms_saq/progress_bar.html"

    def render(self, context, instance, placeholder):
        answered, total = instance.progress_for_user(context['request'].user)
        context.update({
            'answered': answered,
            'total': total,
            'progress': float(answered) / float(total) * 100,
        })
        return context


class BulkAnswerPlugin(CMSPluginBase):
    model = BulkAnswer
    name = "Bulk Answer"
    module = "SAQ"
    render_template = "cms_saq/bulk_answer.html"

    def render(self, context, instance, placeholder):
        context['instance'] = instance
        return context

class SubmissionSetReviewPlugin(CMSPluginBase):
    model = SubmissionSetReview
    name = "Review Submissions"
    module = "SAQ"
    render_template = "cms_saq/submission_set_review.html"

    def render(self, context, instance, placeholder):
        context.update({
            'instance': instance,
            'submission_sets': instance.sets_for_user(user=context['user'])
        })
        return context

plugin_pool.register_plugin(SingleChoiceQuestionPlugin)
plugin_pool.register_plugin(MultiChoiceQuestionPlugin)
plugin_pool.register_plugin(DropDownQuestionPlugin)
plugin_pool.register_plugin(GroupedDropDownQuestionPlugin)
plugin_pool.register_plugin(FreeTextQuestionPlugin)
plugin_pool.register_plugin(FreeNumberQuestionPlugin)
plugin_pool.register_plugin(FormNavPlugin)
plugin_pool.register_plugin(SubmissionSetReviewPlugin)
plugin_pool.register_plugin(SectionedScoringPlugin)
plugin_pool.register_plugin(ProgressBarPlugin)
plugin_pool.register_plugin(BulkAnswerPlugin)
plugin_pool.register_plugin(SessionDefinition)
plugin_pool.register_plugin(QuestionnaireTextPlugin)
plugin_pool.register_plugin(TranslatedTextPlugin)
