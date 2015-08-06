from django import template

from cms_saq.models import (
    Question, Answer, Submission, aggregate_score_for_user_by_tags,
)

register = template.Library()


@register.simple_tag(takes_context=True)
def saq_percent_score(context, question_slug):
    """Get a percentage score for a single question."""
    user = getattr(context['request'], 'user', None)
    try:
        question = Question.objects.get(
            slug=question_slug,
            placeholder__page__publisher_is_draft=False,
        )
    except Question.DoesNotExist:
        return 0
    return int(round(question.percent_score_for_user(user))) or 0


@register.simple_tag(takes_context=True)
def saq_aggregate_percent_score_by_tags(context, tags):
    """Get an aggregate percentage score for a questions grouped by tags."""
    user = getattr(context['request'], 'user', None)
    tags = tags.split(',')
    return int(round(aggregate_score_for_user_by_tags(user, tags)))


@register.simple_tag(takes_context=True)
def saq_raw_answer(context, question_slug):
    """Returns raw answer data -- use to get answers to free-text questions."""
    user = getattr(context['request'], 'user', None)
    try:
        submission = Submission.objects.get(question=question_slug, user=user)
    except Submission.DoesNotExist:
        return ""
    return submission.answer


@register.simple_tag(takes_context=True)
def saq_nice_answer(context, question_slug):
    """Returns 'nice' answer text (looks up titles from Answer objects)."""
    user = getattr(context['request'], 'user', None)
    try:
        submission = Submission.objects.get(question=question_slug, user=user)
    except Submission.DoesNotExist:
        return ""
    try:
        answer = Answer.objects.get(
            question__slug=question_slug, slug=submission.answer,
            question__placeholder__page__publisher_is_draft=False,
        )
    except Answer.DoesNotExist:
        return ""
    return answer.title
