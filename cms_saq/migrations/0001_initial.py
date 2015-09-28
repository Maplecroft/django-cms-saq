# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import cms.models.fields
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('cms', '0003_auto_20140926_2347'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField()),
                ('help_text', models.TextField(null=True, blank=True)),
                ('score', models.IntegerField(default=0)),
                ('order', models.IntegerField(default=0)),
                ('is_default', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('question', 'order', 'slug'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BulkAnswer',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('answer_value', models.CharField(max_length=255)),
                ('label', models.CharField(help_text=b"e.g.: 'mark all as not applicable'", max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='FormNav',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('next_page_label', models.CharField(max_length=255, null=True, blank=True)),
                ('prev_page_label', models.CharField(max_length=255, null=True, blank=True)),
                ('end_page_label', models.CharField(max_length=255, null=True, blank=True)),
                ('submission_set_tag', models.CharField(max_length=255, null=True, blank=True)),
                ('end_page', cms.models.fields.PageField(related_name='formnav_ends', blank=True, to='cms.Page', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='GroupedAnswer',
            fields=[
                ('answer_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms_saq.Answer')),
                ('group', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ('group', 'order', 'slug'),
            },
            bases=('cms_saq.answer',),
        ),
        migrations.CreateModel(
            name='ProgressBar',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('count_optional', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('slug', models.SlugField(help_text=b'A slug for identifying answers to this specific question (allows multiple only for multiple languages)')),
                ('label', models.CharField(max_length=512, blank=True)),
                ('help_text', models.CharField(max_length=512, blank=True)),
                ('question_type', models.CharField(max_length=1, choices=[(b'S', b'Single-choice question'), (b'M', b'Multi-choice question'), (b'F', b'Free-text question')])),
                ('optional', models.BooleanField(default=False, help_text=b'Only applies to free text questions')),
                ('depends_on_answer', models.ForeignKey(related_name='trigger_questions', blank=True, to='cms_saq.Answer', null=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='QuestionnaireText',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('body', models.TextField(verbose_name='body')),
                ('depends_on_answer', models.ForeignKey(related_name='trigger_text', blank=True, to='cms_saq.Answer', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='ScoreSection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255)),
                ('tag', models.CharField(max_length=255)),
                ('order', models.IntegerField()),
            ],
            options={
                'ordering': ('order', 'label'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SectionedScoring',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.SlugField()),
                ('answer', models.TextField(blank=True)),
                ('score', models.IntegerField()),
            ],
            options={
                'ordering': ('submission_set', 'user', 'question'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubmissionSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(blank=True)),
                ('tag', models.SlugField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(related_name='saq_submissions_sets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubmissionSetReview',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin')),
                ('submission_set_tag', models.CharField(max_length=255, null=True, blank=True)),
                ('count_optional', models.BooleanField(default=False)),
                ('label', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
        migrations.AddField(
            model_name='submission',
            name='submission_set',
            field=models.ForeignKey(related_name='submissions', to='cms_saq.SubmissionSet', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='submission',
            name='user',
            field=models.ForeignKey(related_name='saq_submissions', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together=set([('question', 'user', 'submission_set')]),
        ),
        migrations.AddField(
            model_name='scoresection',
            name='group',
            field=models.ForeignKey(related_name='sections', to='cms_saq.SectionedScoring'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formnav',
            name='end_page_condition_question',
            field=models.ForeignKey(blank=True, to='cms_saq.Question', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formnav',
            name='next_page',
            field=cms.models.fields.PageField(related_name='formnav_nexts', blank=True, to='cms.Page', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='formnav',
            name='prev_page',
            field=cms.models.fields.PageField(related_name='formnav_prevs', blank=True, to='cms.Page', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(related_name='answers', to='cms_saq.Question'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together=set([('question', 'slug')]),
        ),
    ]
