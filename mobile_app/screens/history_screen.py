"""
Экран истории посещений студента со статистикой
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.clock import Clock
from services.auth_service import AuthenticationService, UserRole, UserPermission
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class HistoryScreen(Screen):
    """Экран истории посещений и статистики студента"""

    def __init__(self, auth_service: AuthenticationService = None, **kwargs):
        # Извлекаем сервис из kwargs (убираем перед super())
        auth_service = auth_service or kwargs.pop('auth_service', None)
        
        super().__init__(**kwargs)
        self.auth_service = auth_service

        # Основной лейаут
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Заголовок
        title_layout = BoxLayout(size_hint_y=0.15, spacing=dp(10))
        title_label = Label(
            text='[b]История посещений[/b]',
            markup=True,
            font_size='20sp'
        )
        title_layout.add_widget(title_label)

        stats_btn = Button(text='📊', size_hint_x=0.2)
        stats_btn.bind(on_press=self.show_statistics)
        title_layout.add_widget(stats_btn)

        main_layout.add_widget(title_layout)

        # ScrollView с историей
        scroll_view = ScrollView(size_hint_y=0.7)
        self.history_grid = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None,
            padding=dp(5)
        )
        self.history_grid.bind(minimum_height=self.history_grid.setter('height'))
        scroll_view.add_widget(self.history_grid)
        main_layout.add_widget(scroll_view)

        # Кнопки внизу
        button_layout = BoxLayout(size_hint_y=0.15, spacing=dp(10))

        refresh_btn = Button(text='🔄 Обновить')
        refresh_btn.bind(on_press=self.load_history)
        button_layout.add_widget(refresh_btn)

        clear_btn = Button(text='🗑 Очистить')
        clear_btn.bind(on_press=self.clear_history)
        button_layout.add_widget(clear_btn)

        back_btn = Button(text='↩ Назад')
        back_btn.bind(on_press=self.on_back)
        button_layout.add_widget(back_btn)

        main_layout.add_widget(button_layout)
        self.add_widget(main_layout)

    def on_enter(self):
        """Загрузить историю при входе на экран"""
        self.load_history(None)

    def load_history(self, instance):
        """Загрузить историю посещений текущего пользователя"""
        user = self.auth_service.get_current_user()

        # Проверить права
        if not user or not user.has_permission(UserPermission.VIEW_ANALYTICS):
            self.history_grid.clear_widgets()
            label = Label(
                text='У вас нет доступа к истории посещений',
                size_hint_y=None,
                height=dp(50)
            )
            self.history_grid.add_widget(label)
            return

        self.history_grid.clear_widgets()

        if not user.visit_history:
            empty_label = Label(
                text='История посещений пуста',
                size_hint_y=None,
                height=dp(50)
            )
            self.history_grid.add_widget(empty_label)
            return

        # Группировать посещения по датам в обратном порядке (новые первыми)
        visits_by_date = {}
        for visit in reversed(user.visit_history):
            date_key = visit.timestamp.strftime('%d.%m.%Y')
            if date_key not in visits_by_date:
                visits_by_date[date_key] = []
            visits_by_date[date_key].append(visit)

        # Показать историю
        for date, visits in visits_by_date.items():
            # Заголовок даты
            date_label = Label(
                text=f'[b]{date}[/b]',
                markup=True,
                size_hint_y=None,
                height=dp(35),
                background_color=(0.3, 0.6, 1.0, 1.0)
            )
            self.history_grid.add_widget(date_label)

            # Посещения в эту дату
            for visit in visits:
                time_str = visit.timestamp.strftime('%H:%M')
                duration_str = ""
                if visit.duration_seconds:
                    minutes = visit.duration_seconds // 60
                    duration_str = f"\n⏱ {minutes} мин."

                visit_text = f"""[b]{visit.node_name}[/b] (Этаж {visit.floor})
{time_str}{duration_str}
"""
                visit_btn = Button(
                    text=visit_text,
                    markup=True,
                    size_hint_y=None,
                    height=dp(70),
                    background_color=(0.2, 0.2, 0.2, 1.0)
                )
                visit_btn.bind(on_press=lambda x, v=visit: self.show_visit_details(v))
                self.history_grid.add_widget(visit_btn)

    def show_visit_details(self, visit):
        """Показать детали посещения"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        details_text = f"""
[b]Узел:[/b] {visit.node_name}

[b]Этаж:[/b] {visit.floor}

[b]Время посещения:[/b]
{visit.timestamp.strftime('%d.%m.%Y %H:%M:%S')}

[b]Длительность:[/b]
{visit.duration_seconds // 60 if visit.duration_seconds else '?'} минут
"""
        details_label = Label(
            text=details_text,
            markup=True,
            size_hint_y=0.8
        )
        content.add_widget(details_label)

        close_btn = Button(text='Закрыть', size_hint_y=0.2)
        content.add_widget(close_btn)

        popup = Popup(
            title='Детали посещения',
            content=content,
            size_hint=(0.9, 0.6)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_statistics(self, instance):
        """Показать статистику посещений"""
        user = self.auth_service.get_current_user()

        if not user or not user.visit_history:
            return

        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Подсчитать статистику
        total_visits = len(user.visit_history)
        unique_nodes = len(set(v.node_id for v in user.visit_history))
        total_time = sum(v.duration_seconds or 0 for v in user.visit_history)

        # Найти самый посещаемый узел
        node_counts = {}
        for visit in user.visit_history:
            if visit.node_id not in node_counts:
                node_counts[visit.node_id] = {'count': 0, 'name': visit.node_name}
            node_counts[visit.node_id]['count'] += 1

        most_visited = max(node_counts.items(), key=lambda x: x[1]['count'], default=None)

        stats_text = f"""
[b]📊 Статистика посещений[/b]

[b]Всего посещений:[/b] {total_visits}

[b]Уникальных мест:[/b] {unique_nodes}

[b]Общее время:[/b] {total_time // 3600} часов {(total_time % 3600) // 60} минут

[b]Самое часто посещаемое место:[/b]
{most_visited[1]['name'] if most_visited else '—'} ({most_visited[1]['count'] if most_visited else 0} раз)

[b]Последнее посещение:[/b]
{user.visit_history[-1].node_name if user.visit_history else '—'}
"""

        stats_label = Label(
            text=stats_text,
            markup=True,
            size_hint_y=0.8
        )
        content.add_widget(stats_label)

        close_btn = Button(text='Закрыть', size_hint_y=0.2)
        content.add_widget(close_btn)

        popup = Popup(
            title='Статистика',
            content=content,
            size_hint=(0.9, 0.8)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def clear_history(self, instance):
        """Очистить историю (с подтверждением)"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        question = Label(
            text='Вы уверены, что хотите очистить всю историю?',
            size_hint_y=0.6
        )
        content.add_widget(question)

        btn_layout = BoxLayout(size_hint_y=0.4, spacing=dp(10))

        def confirm_clear():
            user = self.auth_service.get_current_user()
            user.visit_history.clear()
            self.auth_service._save_profile(user)
            self.load_history(None)
            popup.dismiss()
            logger.info(f"History cleared for {user.username}")

        yes_btn = Button(text='Да, очистить')
        yes_btn.bind(on_press=lambda x: confirm_clear())
        btn_layout.add_widget(yes_btn)

        no_btn = Button(text='Отмена')
        btn_layout.add_widget(no_btn)

        content.add_widget(btn_layout)

        popup = Popup(
            title='Подтверждение',
            content=content,
            size_hint=(0.8, 0.5)
        )
        no_btn.bind(on_press=popup.dismiss)
        popup.open()

    def on_back(self, instance):
        """Вернуться на домашний экран"""
        self.manager.current = 'home'
