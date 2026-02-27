"""
Компонент для отображения всплывающего меню в нижней части экрана
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.core.window import Window


class BottomPopup(Popup):
    """Всплывающее меню в нижней части экрана"""

    def __init__(self, node=None, on_select_as_start=None, on_select_as_end=None, **kwargs):
        """
        Инициализация Bottom Popup
        
        Args:
            node: Узел для отображения информации
            on_select_as_start: Callback при выборе как стартовой точки
            on_select_as_end: Callback при выборе как конечной точки
        """
        self.node = node
        self.on_select_as_start = on_select_as_start
        self.on_select_as_end = on_select_as_end
        
        # Создаём содержимое попапа
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Информация о узле
        info_layout = GridLayout(cols=2, size_hint_y=0.4, spacing=dp(5))
        
        info_layout.add_widget(Label(text='Узел:', size_hint_x=0.3))
        info_layout.add_widget(Label(text=node.name if node else 'N/A'))
        
        info_layout.add_widget(Label(text='Тип:', size_hint_x=0.3))
        info_layout.add_widget(Label(text=node.node_type if node else 'N/A'))
        
        info_layout.add_widget(Label(text='Этаж:', size_hint_x=0.3))
        info_layout.add_widget(Label(text=str(node.floor) if node else 'N/A'))
        
        content.add_widget(info_layout)
        
        # Кнопки действий
        button_layout = GridLayout(cols=3, size_hint_y=0.4, spacing=dp(5))
        
        start_btn = Button(text='Старт')
        start_btn.bind(on_press=self._on_select_start)
        button_layout.add_widget(start_btn)
        
        end_btn = Button(text='Конец')
        end_btn.bind(on_press=self._on_select_end)
        button_layout.add_widget(end_btn)
        
        close_btn = Button(text='Закрыть')
        close_btn.bind(on_press=self.dismiss)
        button_layout.add_widget(close_btn)
        
        content.add_widget(button_layout)
        
        # Инициализируем Popup
        super().__init__(
            content=content,
            size_hint=(1, 0.25),
            pos_hint={'x': 0, 'y': 0},
            title='Выбор точки',
            **kwargs
        )
    
    def _on_select_start(self, instance):
        """Выбрать как стартовую точку"""
        if self.on_select_as_start:
            self.on_select_as_start(self.node)
        self.dismiss()
    
    def _on_select_end(self, instance):
        """Выбрать как конечную точку"""
        if self.on_select_as_end:
            self.on_select_as_end(self.node)
        self.dismiss()
    
    def open(self, *args, **kwargs):
        """Открыть попап с анимацией"""
        super().open(*args, **kwargs)
        
        # Анимация появления снизу
        anim = Animation(pos_hint={'x': 0, 'y': 0}, duration=0.3)
        anim.start(self)
