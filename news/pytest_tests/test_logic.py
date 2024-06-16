from http import HTTPStatus

import pytest

from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(
    client, news_id_for_args, form_data
):
    url = reverse('news:detail', args=news_id_for_args)
    client.post(url, data=form_data)
    comment_count = Comment.objects.count()
    assert comment_count == 0


def test_user_can_creat_comment(
    author_client, form_data, news_id_for_args,
    author, news
):
    url = reverse('news:detail', args=news_id_for_args)
    response = author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')

    comment_count = Comment.objects.count()
    assert comment_count == 1

    new_comment = Comment.objects.get()
    assert new_comment.text == form_data['text']
    assert new_comment.news == news
    assert new_comment.author == author


def test_user_cant_use_bad_words(author_client, news_id_for_args):
    url = reverse('news:detail', args=news_id_for_args)
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, data=bad_words_data)
    assertFormError(response, 'form', 'text', errors=WARNING)

    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.usefixtures('comment')
def test_author_can_delete_comment(author_client, news_id_for_args):
    detail_url = reverse('news:detail', args=news_id_for_args)
    delete_url = reverse('news:delete', args=news_id_for_args)
    response = author_client.delete(delete_url)
    assertRedirects(response, detail_url + '#comments')


@pytest.mark.usefixtures('comment')
def test_user_cant_delete_comment_of_another_user(
    not_author_client, news_id_for_args
):
    url = reverse('news:delete', args=news_id_for_args)
    response = not_author_client.delete(url)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comment_count = Comment.objects.count()
    assert comment_count == 1


def test_author_can_edit_comment(
    author_client, form_data, comment, news_id_for_args
):
    detail_url = reverse('news:detail', args=news_id_for_args)
    edit_url = reverse('news:edit', args=news_id_for_args)
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, detail_url + '#comments')

    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_user_cant_edit_comment_of_another_user(
    not_author_client, form_data, comment, news_id_for_args
):
    url = reverse('news:edit', args=news_id_for_args)
    response = not_author_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comment_from_db = Comment.objects.get(id=comment.id)
    comment.refresh_from_db()
    assert comment_from_db.text == comment.text
