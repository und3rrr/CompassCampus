"""
Современный интерактивный Bottom Sheet для выбора точек маршрута
Может скользить вверх/вниз и остаётся полупрозрачным
"""
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.animation import Animation
import logging

logger = logging.getLogger(__name__)


class ModernBottomSheet(FloatLayout):
    """Интерактивный bottom sheet на треть экрана"""

    def __init__(self, node=None, on_from_selected=None, on_to_selected=None, on_close=None, **kwargs):
        """
        Args:
            node: Узел для отображения
            on_from_selected: Callback при выборе как "ОТСЮДА"
            on_to_selected: Callback при выборе как "СЮДА"
            on_close: Callback при закрытии
        """
        super().__init__(**kwargs)
        self.node = node
        self.on_from_selected = on_from_selected
        self.on_to_selected = on_to_selected
        self.on_close = on_close
        
        self.is_expanded = False
        
        # Полупрозрачный оверлей (поглощает клики если нажать вне sheet)
        self.overlay = FloatLayout(size_hint=(1, 1))
        self.overlay.bind(on_touch_down=self._on_overlay_touch)
        self.add_widget(self.overlay)
        
        # Основной sheet контейнер
        sheet_container = FloatLayout(
            size_hint=(1, 0.35),  # 35% экрана (треть)
            pos_hint={'x': 0, 'y': 0}
        )
        
        # Фон sheet
        with sheet_container.canvas.before:
            Color(1, 1, 1, 0.95)  # Белый с прозрачностью
            self.sheet_bg = RoundedRectangle(
                size=sheet_container.size,
                pos=sheet_container.pos,
                radius=[dp(20), dp(20), 0, 0]
            )
        
        sheet_container.bind(size=self._update_sheet_bg, pos=self._update_sheet_bg)
        
        # Содержимое sheet
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Ручка для перетаскивания (визуальный элемент)
        handle_box = BoxLayout(size_hint_y=None, height=dp(20))
        handle_box.add_widget(Widget())  # Левый спейсер
        with handle_box.canvas.before:
            Color(0.8, 0.8, 0.8, 0.5)
            handle = RoundedRectangle(size=(dp(40), dp(5)), pos=(0, 0))
            handle_box.canvas.before.add(handle)
        handle_box.add_widget(Widget())  # Правый спейсер
        content.add_widget(handle_box)
        
        # Название узла (большой шрифт)
        title = Label(
            text=node.name if node else 'N/A',
            size_hint_y=None,
            height=dp(40),
            font_size='20sp',
            bold=True,
            color=(0.1, 0.1, 0.1, 1.0)
        )
        content.add_widget(title)
        
        # Информация о узле (тип и этаж)
        info_layout = GridLayout(
            cols=2,
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10),
            padding=dp(5)
        )
        
        # Тип
        info_layout.add_widget(Label(
            text='[b]Тип:[/b]',
            markup=True,
            size_hint_x=0.3,
            font_size='12sp',
            color=(0.3, 0.3, 0.3, 1.0)
        ))
        info_layout.add_widget(Label(
            text=node.node_type if node else 'N/A',
            size_hint_x=0.7,
            font_size='12sp',
            color=(0.1, 0.1, 0.1, 1.0)
        ))
        
        # Этаж
        info_layout.add_widget(Label(
            text='[b]Этаж:[/b]',
            markup=True,
            size_hint_x=0.3,
            font_size='12sp',
            color=(0.3, 0.3, 0.3, 1.0)
        ))
        info_layout.add_widget(Label(
            text=str(node.floor) if node else 'N/A',
            size_hint_x=0.7,
            font_size='12sp',
            color=(0.1, 0.1, 0.1, 1.0)
        ))
        
        content.add_widget(info_layout)
        
        # Кнопки действий - большие, современные
        button_layout = GridLayout(cols=2, size_hint_y=None, height=dp(60), spacing=dp(10))
        
        # Кнопка "ОТСЮДА" (зелёная)
        from_btn = Button(
            text='Отсюда',
            background_color=(0.2, 0.8, 0.3, 1.0),
            color=(1, 1, 1, 1.0),
            font_size='14sp',
            bold=True
        )
        from_btn.bind(on_press=self._on_from_selected)
        button_layout.add_widget(from_btn)
        
        # Кнопка "СЮДА" (синяя)
        to_btn = Button(
            text='Сюда',
            background_color=(0.2, 0.4, 0.9, 1.0),
            color=(1, 1, 1, 1.0),
            font_size='14sp',
            bold=True
        )
        to_btn.bind(on_press=self._on_to_selected)
        button_layout.add_widget(to_btn)
        
        content.add_widget(button_layout)
        
        sheet_container.add_widget(content)
        self.add_widget(sheet_container)
        self.sheet_container = sheet_container

    def _update_sheet_bg(self, instance, value):
        """Обновить фон sheet при изменении размера"""
        self.sheet_bg.size = instance.size
        self.sheet_bg.pos = instance.pos

    def _on_overlay_touch(self, instance, touch):
        """Закрыть sheet при клике на оверлей (вне sheet)"""
        if not self.sheet_container.collide_point(*touch.pos):
            self.close()
            return True
        return False

    def _on_from_selected(self, instance):
        """Выбрать как ОТСЮДА"""
        if self.on_from_selected:
            self.on_from_selected(self.node)
        self.close()

    def _on_to_selected(self, instance):
        """Выбрать как СЮДА"""
        if self.on_to_selected:
            self.on_to_selected(self.node)
        self.close()

    def open(self):
        """Открыть sheet с анимацией"""
        # Анимация появления снизу
        anim = Animation(y=0, duration=0.3)
        anim.start(self.sheet_container)

    def close(self):
        """Закрыть sheet с анимацией"""
        anim = Animation(y=-self.height * 0.5, duration=0.3)
        anim.bind(on_complete=lambda *args: self._remove_from_parent())
        anim.start(self.sheet_container)

    def _remove_from_parent(self):
        """Удалить из родительского виджета"""
        if self.parent:
            self.parent.remove_widget(self)
        if self.on_close:
            self.on_close()
