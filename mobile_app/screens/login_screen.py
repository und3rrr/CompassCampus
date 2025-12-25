"""
Экран входа/авторизации
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.clock import Clock
from services.auth_service import AuthenticationService, UserRole
import logging

logger = logging.getLogger(__name__)


class LoginScreen(Screen):
    """Экран входа для различных типов пользователей"""

    def __init__(self, auth_service: AuthenticationService = None, **kwargs):
        # Извлекаем сервис из kwargs если он там есть
        if auth_service is None:
            auth_service = kwargs.pop('auth_service', None)
        
        super().__init__(**kwargs)
        self.auth_service = auth_service
        self.current_mode = 'guest'
        
        self.main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Заголовок
        title_label = Label(
            text='[b]CampusCompass[/b]\nНавигация по кампусу',
            markup=True,
            size_hint_y=0.12,
            font_size='24sp'
        )
        self.main_layout.add_widget(title_label)
        
        # Если есть последний пользователь, показать кнопку быстрого входа
        if auth_service.current_user:
            quick_login_layout = BoxLayout(size_hint_y=0.08, spacing=dp(5))
            quick_login_label = Label(
                text=f'Запомнённый пользователь: {auth_service.current_user.username}',
                size_hint_x=0.7
            )
            quick_login_layout.add_widget(quick_login_label)
            
            quick_login_btn = Button(text='Войти', size_hint_x=0.3)
            quick_login_btn.bind(on_press=self.on_quick_login)
            quick_login_layout.add_widget(quick_login_btn)
            self.main_layout.add_widget(quick_login_layout)

        # Выбор типа входа
        mode_layout = BoxLayout(size_hint_y=0.08, spacing=dp(5))
        mode_label = Label(text='Новый вход:', size_hint_x=0.3)
        mode_layout.add_widget(mode_label)
        
        self.mode_spinner = Spinner(
            text='Гост',
            values=('Гост', 'Студент', 'Администратор'),
            size_hint_x=0.7
        )
        self.mode_spinner.bind(text=self.on_mode_changed)
        mode_layout.add_widget(self.mode_spinner)
        self.main_layout.add_widget(mode_layout)

        # Контейнер для содержимого
        self.content_container = BoxLayout(orientation='vertical', size_hint_y=0.50)
        self.main_layout.add_widget(self.content_container)

        # Кнопки внизу
        button_layout = BoxLayout(size_hint_y=0.15, spacing=dp(10))
        
        self.login_btn = Button(text='Войти')
        self.login_btn.bind(on_press=self.on_login)
        button_layout.add_widget(self.login_btn)
        
        exit_btn = Button(text='Выход')
        exit_btn.bind(on_press=self.on_exit)
        button_layout.add_widget(exit_btn)
        
        self.main_layout.add_widget(button_layout)
        self.add_widget(self.main_layout)
        
        # Инициализируем с режимом гостя
        self.on_mode_changed(self.mode_spinner, 'Гост')

    def on_mode_changed(self, spinner, text):
        """Изменить режим входа"""
        self.current_mode = text.lower()
        self.content_container.clear_widgets()
        
        if text == 'Гост':
            self.content_container.add_widget(self._create_guest_form())
        elif text == 'Студент':
            self.content_container.add_widget(self._create_student_form())
        elif text == 'Администратор':
            self.content_container.add_widget(self._create_admin_form())

    def _create_guest_form(self) -> BoxLayout:
        """Создать форму для гостя"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        info_label = Label(
            text='Вы можете просмотреть карту\nи навигацию без регистрации',
            size_hint_y=1.0,
            markup=True
        )
        layout.add_widget(info_label)
        
        return layout

    def _create_student_form(self) -> BoxLayout:
        """Создать форму для студента"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Имя
        layout.add_widget(Label(text='Имя:', size_hint_y=0.1))
        self.student_name = TextInput(hint_text='Введите имя', multiline=False, size_hint_y=0.15)
        layout.add_widget(self.student_name)
        
        # Email
        layout.add_widget(Label(text='Email:', size_hint_y=0.1))
        self.student_email = TextInput(hint_text='example@edu.ru', multiline=False, size_hint_y=0.15)
        layout.add_widget(self.student_email)
        
        # ID студента
        layout.add_widget(Label(text='ID студента:', size_hint_y=0.1))
        self.student_id = TextInput(hint_text='123456', multiline=False, size_hint_y=0.15)
        layout.add_widget(self.student_id)
        
        layout.add_widget(Label(text='', size_hint_y=0.35))  # Пространство
        
        return layout

    def _create_admin_form(self) -> BoxLayout:
        """Создать форму для администратора"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Имя
        layout.add_widget(Label(text='Имя:', size_hint_y=0.08))
        self.admin_name = TextInput(hint_text='Имя администратора', multiline=False, size_hint_y=0.12)
        layout.add_widget(self.admin_name)
        
        # Email
        layout.add_widget(Label(text='Email:', size_hint_y=0.08))
        self.admin_email = TextInput(hint_text='admin@edu.ru', multiline=False, size_hint_y=0.12)
        layout.add_widget(self.admin_email)
        
        # ID
        layout.add_widget(Label(text='ID администратора:', size_hint_y=0.08))
        self.admin_id = TextInput(hint_text='admin_123', multiline=False, size_hint_y=0.12)
        layout.add_widget(self.admin_id)
        
        # Пароль
        layout.add_widget(Label(text='Пароль:', size_hint_y=0.08))
        self.admin_password = TextInput(hint_text='Пароль', password=True, multiline=False, size_hint_y=0.12)
        layout.add_widget(self.admin_password)
        
        layout.add_widget(Label(text='', size_hint_y=0.22))  # Пространство
        
        return layout

    def on_login(self, instance):
        """Обработка входа"""
        try:
            if self.current_mode == 'гост':
                profile = self.auth_service.login_as_guest()
                logger.info("Guest logged in")
            elif self.current_mode == 'студент':
                name = self.student_name.text.strip()
                email = self.student_email.text.strip()
                student_id = self.student_id.text.strip()
                
                if not all([name, email, student_id]):
                    self._show_error("Заполните все поля")
                    return
                
                profile = self.auth_service.login_student(name, email, student_id)
                logger.info(f"Student logged in: {name}")
            elif self.current_mode == 'администратор':
                name = self.admin_name.text.strip()
                email = self.admin_email.text.strip()
                admin_id = self.admin_id.text.strip()
                password = self.admin_password.text.strip()
                
                if not all([name, email, admin_id, password]):
                    self._show_error("Заполните все поля")
                    return
                
                profile = self.auth_service.login_admin(name, email, admin_id, password)
                logger.info(f"Admin logged in: {name}")
            
            self.manager.current = 'home'
        except Exception as e:
            logger.error(f"Login error: {e}")
            self._show_error(f"Ошибка входа: {str(e)}")

    def on_quick_login(self, instance):
        """Быстрый вход с сохранённым пользователем"""
        if self.auth_service.current_user:
            self.manager.current = 'home'

    def on_exit(self, instance):
        """Выход из приложения"""
        import sys
        sys.exit()

    def _show_error(self, message: str):
        """Показать ошибку"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        label = Label(text=message)
        content.add_widget(label)
        
        btn = Button(text='OK', size_hint_y=0.3)
        content.add_widget(btn)
        
        popup = Popup(title='Ошибка', content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        popup.open()
