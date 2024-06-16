import pytest

from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm

@pytest.mark.django_db
@pytest.mark.usefixtures('list_of_news')
class TestHomePage:
    HOME_URL = reverse('news:home')

    def test_news_count(self, client):
        response = client.get(self.HOME_URL)
        object_list = response.context['object_list']
        news_count = object_list.count()
        assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE

    def test_news_order(self, client):
        response = client.get(self.HOME_URL)
        object_list = response.context['object_list']
        all_dates = [news.date for news in object_list]
        sorted_dates = sorted(all_dates, reverse=True)
        assert all_dates == sorted_dates


@pytest.mark.usefixtures('comments_under_news')
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:detail', pytest.lazy_fixture('news_id_for_args')),
    ),
)
class TestDetailPage:
    def test_comments_order(self, client, name, args):
        detail_url = reverse(name, args=args)
        response = client.get(detail_url)
        assert 'news' in response.context

        news = response.context['news']
        all_comments = news.comment_set.all()
        all_timestamps = [comment.created for comment in all_comments]
        sorted_timestamps = sorted(all_timestamps)
        assert all_timestamps == sorted_timestamps

    def test_anonymous_client_has_no_form(self, client, name, args):
        detail_url = reverse(name, args=args)
        response = client.get(detail_url)
        assert 'form' not in response.context

    def test_authorized_client_has_form(self, author_client, name, args):
        detail_url = reverse(name, args=args)
        response = author_client.get(detail_url)
        assert 'form' in response.context
        # Проверим, что объект формы соответствует нужному классу формы.
        assert isinstance(response.context['form'], CommentForm)
