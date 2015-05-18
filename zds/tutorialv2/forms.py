# coding: utf-8
from django import forms
from django.conf import settings

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout, Submit, Field, ButtonHolder, Hidden
from django.core.urlresolvers import reverse

from zds.utils.forms import CommonLayoutModalText, CommonLayoutEditor, CommonLayoutVersionEditor
from zds.utils.models import SubCategory, Licence
from zds.tutorialv2.models import TYPE_CHOICES
from zds.utils.models import HelpWriting
from zds.tutorialv2.models.models_database import PublishableContent
from django.utils.translation import ugettext_lazy as _
from zds.member.models import Profile


class FormWithTitle(forms.Form):
    title = forms.CharField(
        label=_(u'Titre'),
        max_length=PublishableContent._meta.get_field('title').max_length,
        widget=forms.TextInput(
            attrs={
                'required': 'required',
            }
        )
    )

    def clean(self):
        cleaned_data = super(FormWithTitle, self).clean()

        title = cleaned_data.get('title')

        if title is not None and title.strip() == '':
            self._errors['title'] = self.error_class(
                [_(u'Le champ du titre ne peut être vide.')])
            if 'title' in cleaned_data:
                del cleaned_data['title']

        return cleaned_data


class AuthorForm(forms.Form):

    username = forms.CharField(
        label=_(u"Auteurs à ajouter séparés d'une virgule"),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(AuthorForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username'),
            ButtonHolder(
                StrictButton(_('Ajouter'), type='submit'),
            )
        )

    def clean(self):
        """Check every username and send it to the cleaned_data["user"] list

        :return: a dictionary of all treated data with the users key added
        """
        cleaned_data = super(AuthorForm, self).clean()
        users = []
        for username in cleaned_data.get('username').split(","):
            user = Profile.objects.contactable_members().filter(user__username__iexact=username.strip().lower()).first()
            if user is not None:
                users.append(user.user)
        if len(users) > 0:
            cleaned_data["users"] = users
        return cleaned_data

    def is_valid(self):
        return super(AuthorForm, self).is_valid() and "users" in self.clean()


class ContainerForm(FormWithTitle):

    introduction = forms.CharField(
        label=_(u"Introduction"),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    conclusion = forms.CharField(
        label=_(u"Conclusion"),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    msg_commit = forms.CharField(
        label=_(u"Message de suivi"),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications')
            }
        )
    )

    last_hash = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(ContainerForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('introduction', css_class='md-editor'),
            Field('conclusion', css_class='md-editor'),
            Field('msg_commit'),
            Field('last_hash'),
            ButtonHolder(
                StrictButton(
                    _(u'Valider'),
                    type='submit'),
            )
        )


class ContentForm(ContainerForm):

    description = forms.CharField(
        label=_(u'Description'),
        max_length=PublishableContent._meta.get_field('description').max_length,
        required=False,
    )

    image = forms.ImageField(
        label=_(u'Sélectionnez le logo du tutoriel (max. {} Ko)').format(
            str(settings.ZDS_APP['gallery']['image_max_size'] / 1024)),
        required=False
    )

    type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False
    )

    subcategory = forms.ModelMultipleChoiceField(
        label=_(u"Sous catégories de votre tutoriel. Si aucune catégorie ne convient "
                u"n'hésitez pas à en demander une nouvelle lors de la validation !"),
        queryset=SubCategory.objects.all(),
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                'required': 'required',
            }
        )
    )

    licence = forms.ModelChoiceField(
        label=(
            _(u'Licence de votre publication (<a href="{0}" alt="{1}">En savoir plus sur les licences et {2}</a>)')
            .format(
                settings.ZDS_APP['site']['licenses']['licence_info_title'],
                settings.ZDS_APP['site']['licenses']['licence_info_link'],
                settings.ZDS_APP['site']['name']
            )
        ),
        queryset=Licence.objects.all(),
        required=True,
        empty_label=None
    )

    helps = forms.ModelMultipleChoiceField(
        label=_(u"Pour m'aider je cherche un..."),
        queryset=HelpWriting.objects.all(),
        required=False,
        widget=forms.SelectMultiple()
    )

    def __init__(self, *args, **kwargs):
        super(ContentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('description'),
            Field('type'),
            Field('image'),
            Field('introduction', css_class='md-editor'),
            Field('conclusion', css_class='md-editor'),
            Field('last_hash'),
            Field('licence'),
            Field('subcategory'),
            HTML(_(u"<p>Demander de l'aide à la communauté !<br>"
                   u"Si vous avez besoin d'un coup de main,"
                   u"sélectionnez une ou plusieurs catégories d'aide ci-dessous "
                   u"et votre tutoriel apparaitra alors sur <a href="
                   u"\"{% url \"zds.tutorial.views.help_tutorial\" %}\" "
                   u"alt=\"aider les auteurs\">la page d'aide</a>.</p>")),
            Field('helps'),
            Field('msg_commit'),
            ButtonHolder(
                StrictButton('Valider', type='submit'),
            ),
        )

        if 'type' in self.initial:
            self.helper['type'].wrap(
                Field,
                disabled=True)


class ExtractForm(FormWithTitle):

    text = forms.CharField(
        label=_(u'Texte'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.')
            }
        )
    )

    msg_commit = forms.CharField(
        label=_(u"Message de suivi"),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications')
            }
        )
    )

    last_hash = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(ExtractForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('last_hash'),
            CommonLayoutVersionEditor(),
        )


class ImportForm(forms.Form):

    file = forms.FileField(
        label=_(u'Sélectionnez le tutoriel à importer'),
        required=True
    )
    images = forms.FileField(
        label=_(u'Fichier zip contenant les images du tutoriel'),
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('file'),
            Field('images'),
            Submit('import-tuto', _(u'Importer le .tuto')),
        )
        super(ImportForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ImportForm, self).clean()

        # Check that the files extensions are correct
        tuto = cleaned_data.get('file')
        images = cleaned_data.get('images')

        if tuto is not None:
            ext = tuto.name.split(".")[-1]
            if ext != "tuto":
                del cleaned_data['file']
                msg = _(u'Le fichier doit être au format .tuto')
                self._errors['file'] = self.error_class([msg])

        if images is not None:
            ext = images.name.split(".")[-1]
            if ext != "zip":
                del cleaned_data['images']
                msg = _(u'Le fichier doit être au format .zip')
                self._errors['images'] = self.error_class([msg])


class ImportContentForm(forms.Form):

    archive = forms.FileField(
        label=_(u"Sélectionnez l'archive de votre tutoriel"),
        required=True
    )
    image_archive = forms.FileField(
        label=_(u"Sélectionnez l'archive des images"),
        required=False
    )

    msg_commit = forms.CharField(
        label=_(u"Message de suivi"),
        max_length=80,
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'Un résumé de vos ajouts et modifications')
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ImportContentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('archive'),
            Field('image_archive'),
            Field('msg_commit'),
            ButtonHolder(
                StrictButton('Importer l\'archive', type='submit'),
            ),
        )

    def clean(self):
        cleaned_data = super(ImportContentForm, self).clean()

        # Check that the files extensions are correct
        archive = cleaned_data.get('archive')

        if archive is not None:
            ext = archive.name.split(".")[-1]
            if ext != 'zip':
                del cleaned_data['archive']
                msg = _(u'L\'archive doit être au format ZIP')
                self._errors['archive'] = self.error_class([msg])

        return cleaned_data


class ImportNewContentForm(ImportContentForm):

    subcategory = forms.ModelMultipleChoiceField(
        label=_(u"Sous catégories de votre contenu. Si aucune catégorie ne convient "
                u"n'hésitez pas à en demander une nouvelle lors de la validation !"),
        queryset=SubCategory.objects.all(),
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                'required': 'required',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ImportContentForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'content-wrapper'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('archive'),
            Field('subcategory'),
            Field('msg_commit'),
            ButtonHolder(
                StrictButton('Importer l\'archive', type='submit'),
            ),
        )


class BetaForm(forms.Form):
    version = forms.CharField(widget=forms.HiddenInput, required=True)

# Notes


class NoteForm(forms.Form):
    text = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Votre message au format Markdown.'),
                'required': 'required'
            }
        )
    )

    def __init__(self, content, reaction, *args, **kwargs):
        super(NoteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('content:add-reaction') + u'?pk={}'.format(content.pk)
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            Hidden('last_note', '{{ last_note_pk }}'),
        )

        if content.antispam:
            if not reaction:
                self.helper['text'].wrap(
                    Field,
                    placeholder=_(u'Vous venez de poster. Merci de patienter '
                                  u'au moins 15 minutes entre deux messages consécutifs '
                                  u'afin de limiter le flood.'),
                    disabled=True)
        elif content.is_locked:
            self.helper['text'].wrap(
                Field,
                placeholder=_(u'Ce tutoriel est verrouillé.'),
                disabled=True
            )
        if reaction is not None:
            self.initial.setdefault("text", reaction.text)

    def clean(self):
        cleaned_data = super(NoteForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or text.strip() == '':
            self._errors['text'] = self.error_class(
                [_(u'Vous devez écrire une réponse !')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) > settings.ZDS_APP['forum']['max_post_length']:
            self._errors['text'] = self.error_class(
                [_(u'Ce message est trop long, il ne doit pas dépasser {0} '
                   u'caractères').format(settings.ZDS_APP['forum']['max_post_length'])])

        return cleaned_data


class NoteEditForm(NoteForm):

    def __init__(self, *args, **kwargs):
        super(NoteEditForm, self).__init__(*args, **kwargs)

        content = kwargs['content']
        reaction = kwargs['reaction']

        self.helper.form_action = \
            reverse('content:update-reaction') + u'?message={}&pk={}'.format(reaction.pk, content.pk)


# Validations.

class AskValidationForm(forms.Form):

    text = forms.CharField(
        label='',
        required=False,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Commentaire pour votre demande.'),
                'rows': '3'
            }
        )
    )
    source = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'URL de la version originale')
            }
        )
    )

    version = forms.CharField(widget=forms.HiddenInput(), required=True)

    previous_page_url = ''

    def __init__(self, content, *args, **kwargs):
        super(AskValidationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url() + '?version=' + content.current_version

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:ask', kwargs={'pk': content.pk, 'slug': content.slug})
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('source'),
            Field('version'),
            StrictButton(
                _(u'Confirmer'),
                type='submit')
        )

    def clean(self):
        cleaned_data = super(AskValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or text.strip() == '':
            self._errors['text'] = self.error_class(
                [_(u'Vous devez fournir un commentaire aux validateurs.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class AcceptValidationForm(forms.Form):

    validation = None

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Commentaire de publication.'),
                'rows': '2'
            }
        )
    )

    is_major = forms.BooleanField(
        label=_(u'Version majeure ?'),
        required=False,
        initial=True
    )

    source = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _(u'URL de la version originale')
            }
        )
    )

    def __init__(self, validation, *args, **kwargs):

        # modal form, send back to previous page:
        self.previous_page_url = reverse(
            'content:view',
            kwargs={
                'pk': validation.content.pk,
                'slug': validation.content.slug
            }) + '?version=' + validation.version

        super(AcceptValidationForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:accept', kwargs={'pk': validation.pk})
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('source'),
            Field('is_major'),
            StrictButton(_(u'Publier'), type='submit')
        )

    def clean(self):
        cleaned_data = super(AcceptValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or text.strip() == '':
            self._errors['text'] = self.error_class(
                [_(u'Vous devez fournir un commentaire aux validateurs.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class CancelValidationForm(forms.Form):

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Pourquoi annuler la validation ?'),
                'rows': '4'
            }
        )
    )

    def __init__(self, validation, *args, **kwargs):
        super(CancelValidationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = reverse(
            'content:view',
            kwargs={
                'pk': validation.content.pk,
                'slug': validation.content.slug
            }) + '?version=' + validation.version

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:cancel', kwargs={'pk': validation.pk})
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            HTML("<p>Êtes-vous certain d'annuler la validation de ce contenu ?</p>"),
            CommonLayoutModalText(),
            ButtonHolder(
                StrictButton(
                    _(u'Confirmer'),
                    type='submit'))
        )

    def clean(self):
        cleaned_data = super(CancelValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or text.strip() == '':
            self._errors['text'] = self.error_class(
                [_(u'Merci de fournir une raison à l\'annulation.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class RejectValidationForm(forms.Form):

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Commentaire de rejet.'),
                'rows': '6'
            }
        )
    )

    def __init__(self, validation, *args, **kwargs):
        super(RejectValidationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = reverse(
            'content:view',
            kwargs={
                'pk': validation.content.pk,
                'slug': validation.content.slug
            }) + '?version=' + validation.version

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:reject', kwargs={'pk': validation.pk})
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            ButtonHolder(
                StrictButton(
                    _(u'Rejeter'),
                    type='submit'))
        )

    def clean(self):
        cleaned_data = super(RejectValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or text.strip() == '':
            self._errors['text'] = self.error_class(
                [_(u'Merci de fournir une raison au rejet.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class RevokeValidationForm(forms.Form):

    version = forms.CharField(widget=forms.HiddenInput())

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Pourquoi dépublier ce contenu ?'),
                'rows': '6'
            }
        )
    )

    def __init__(self, content, *args, **kwargs):
        super(RevokeValidationForm, self).__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse('validation:revoke', kwargs={'pk': content.pk, 'slug': content.slug})
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            CommonLayoutModalText(),
            Field('version'),
            StrictButton(
                _(u'Dépublier'),
                type='submit')
        )

    def clean(self):
        cleaned_data = super(RevokeValidationForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or text.strip() == '':
            self._errors['text'] = self.error_class(
                [_(u'Veuillez entrer la raison de votre dépublication.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data


class JsFiddleActivationForm(forms.Form):

    js_support = forms.BooleanField(
        label='Cocher pour activer JSFiddle',
        required=False,
        initial=True
    )

    def __init__(self, *args, **kwargs):
        super(JsFiddleActivationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('content:activate-jsfiddle')
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('js_support'),
            ButtonHolder(
                StrictButton(
                    _(u'Valider'),
                    type='submit'),),
            Hidden('pk', '{{ content.pk }}'), )

    def clean(self):
        cleaned_data = super(JsFiddleActivationForm, self).clean()
        if "js_support" not in cleaned_data:
            cleaned_data["js_support"] = False
        if "pk" in self.data and self.data["pk"].isdigit():
            cleaned_data["pk"] = int(self.data["pk"])
        else:
            cleaned_data["pk"] = 0
        return cleaned_data


class MoveElementForm(forms.Form):

    child_slug = forms.HiddenInput()
    container_slug = forms.HiddenInput()
    first_level_slug = forms.HiddenInput()
    moving_method = forms.HiddenInput()

    MOVE_UP = "up"
    MOVE_DOWN = "down"
    MOVE_AFTER = "after"
    MOVE_BEFORE = "before"

    def __init__(self, *args, **kwargs):
        super(MoveElementForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('content:move-element')
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('child_slug'),
            Field('container_slug'),
            Field('first_level_slug'),
            Field('moving_method'),
            Hidden('pk', '{{ content.pk }}'))


class WarnTypoForm(forms.Form):

    text = forms.CharField(
        label='',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': _(u'Expliquez la faute'),
                'rows': '3'
            }
        )
    )

    target = forms.CharField(widget=forms.HiddenInput(), required=False)
    version = forms.CharField(widget=forms.HiddenInput(), required=True)

    def __init__(self, content, targeted, public=True, *args, **kwargs):
        super(WarnTypoForm, self).__init__(*args, **kwargs)

        self.content = content
        self.targeted = targeted

        # modal form, send back to previous page if any:
        if public:
            self.previous_page_url = targeted.get_absolute_url_online()
        else:
            self.previous_page_url = targeted.get_absolute_url_beta()

        # add an additional link to send PM if needed
        type_ = _(u'l\'article') if content.type == 'ARTICLE' else _(u'le tutoriel')

        if targeted.get_tree_depth() == 0:
            pm_title = _(u'J\'ai trouvé une faute dans {} « {} »').format(type_, targeted.title)
        else:
            pm_title = _(u'J\'ai trouvé une faute dans le chapitre « {} »').format(targeted.title)

        usernames = ''
        num_of_authors = content.authors.count()
        for index, user in enumerate(content.authors.all()):
            if index != 0:
                usernames += '&'
            usernames += 'username=' + user.username

        msg = _(u'<p>Pas assez de place ? <a href="{}?title={}&{}">Envoyez un MP {}</a> !</a>').format(
            reverse('mp-new'), pm_title, usernames, _(u'à l\'auteur') if num_of_authors == 1 else _(u'aux auteurs')
        )

        version = content.sha_beta
        if public:
            version = content.sha_public

        # create form
        self.helper = FormHelper()
        self.helper.form_action = reverse('content:warn-typo') + '?pk={}'.format(content.pk)
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('target'),
            Field('text'),
            HTML(msg),
            Hidden('pk', '{{ content.pk }}'),
            Hidden('version', version),
            ButtonHolder(StrictButton(_(u'Envoyer'), type='submit'))
        )

    def clean(self):
        cleaned_data = super(WarnTypoForm, self).clean()

        text = cleaned_data.get('text')

        if text is None or text.strip() == '':
            self._errors['text'] = self.error_class(
                [_(u'Vous devez indiquer la faute commise.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        elif len(text) < 3:
            self._errors['text'] = self.error_class(
                [_(u'Votre commentaire doit faire au moins 3 caractères.')])
            if 'text' in cleaned_data:
                del cleaned_data['text']

        return cleaned_data
