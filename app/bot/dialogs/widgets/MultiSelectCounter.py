from typing import Generic, Optional, Union, Callable, Dict, List, TypeVar
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.api.internal import RawKeyboard
from aiogram_dialog.widgets.common import (
    ManagedWidget
)
from aiogram_dialog.widgets.common.items import ItemsGetterVariant
from aiogram_dialog.widgets.kbd.select import StatefulSelect, ItemIdGetter, OnItemClick, OnItemStateChanged, TypeFactory
from aiogram_dialog.widgets.text import Text, Format, Case
from aiogram_dialog.dialog import DialogProtocol, ChatEvent
from aiogram_dialog.widgets.widget_event import WidgetEventProcessor, ensure_event_processor

T = TypeVar("T")

# Константы для Counter
PLUS_TEXT = Format("➕")
MINUS_TEXT = Format("➖")
DEFAULT_COUNTER_TEXT = Format("{value:.0f}")


class MultiSelectCounter(StatefulSelect[T], Generic[T]):
    """
    Виджет, который объединяет Multiselect и Counter.
    Каждый элемент имеет кнопку выбора и счетчик.
    """

    def __init__(
            self,
            checked_text: Text,
            unchecked_text: Text,
            id: str,
            item_id_getter: ItemIdGetter,
            items: ItemsGetterVariant,
            min_selected: int = 0,
            max_selected: int = 0,
            # Параметры для Counter
            counter_plus: Optional[Text] = PLUS_TEXT,
            counter_minus: Optional[Text] = MINUS_TEXT,
            counter_text: Optional[Text] = DEFAULT_COUNTER_TEXT,
            counter_min_value: float = 0,
            counter_max_value: float = 999999,
            counter_increment: float = 1,
            counter_cycle: bool = False,
            counter_default: float = 0,
            # Обработчики событий
            on_click: Union[
                OnItemClick["ManagedMultiSelectCounter[T]", T],
                WidgetEventProcessor, None,
            ] = None,
            on_state_changed: Union[
                OnItemStateChanged["ManagedMultiSelectCounter[T]", T],
                WidgetEventProcessor, None,
            ] = None,
            on_counter_click: WidgetEventProcessor = None,
            on_counter_text_click: WidgetEventProcessor = None,
            on_counter_value_changed: WidgetEventProcessor = None,
            when: Optional[Union[str, Callable]] = None,
            type_factory: TypeFactory[T] = str,
    ):
        super().__init__(
            checked_text=checked_text,
            unchecked_text=unchecked_text,
            item_id_getter=item_id_getter,
            items=items,
            on_click=on_click,
            on_state_changed=on_state_changed,
            id=id, when=when, type_factory=type_factory,
        )
        self.min_selected = min_selected
        self.max_selected = max_selected

        # Сохраняем тексты для кнопок выбора
        self.checked_text = checked_text
        self.unchecked_text = unchecked_text

        # Параметры для Counter
        self.counter_plus = counter_plus
        self.counter_minus = counter_minus
        self.counter_text = counter_text
        self.counter_min = counter_min_value
        self.counter_max = counter_max_value
        self.counter_increment = counter_increment
        self.counter_cycle = counter_cycle
        self.counter_default = counter_default

        # Обработчики для Counter
        self.on_counter_click = ensure_event_processor(on_counter_click)
        self.on_counter_text_click = ensure_event_processor(on_counter_text_click)
        self.on_counter_value_changed = ensure_event_processor(on_counter_value_changed)

    def _is_text_checked(
            self, data: dict, case: Case, manager: DialogManager,
    ) -> bool:
        item_id = str(self.item_id_getter(data["item"]))
        if manager.is_preview():
            return ord(item_id[-1]) % 2 == 1
        return self.is_checked(item_id, manager)

    def _get_counters_data(self, manager: DialogManager) -> Dict[str, float]:
        """Получить данные счетчиков в виде {item_id: count}"""
        return self.get_widget_data(manager, {})

    def _set_counters_data(self, manager: DialogManager, data: Dict[str, float]):
        """Установить данные счетчиков"""
        self.set_widget_data(manager, data)

    def get_counter_value(self, item_id: T, manager: DialogManager) -> float:
        """Получить значение счетчика для элемента"""
        counters = self._get_counters_data(manager)
        item_id_str = str(item_id)
        return counters.get(item_id_str, self.counter_default)

    async def set_counter_value(
            self, event: ChatEvent, item_id: T, value: float, manager: DialogManager
    ) -> None:
        """Установить значение счетчика для элемента"""
        if value == 0 or (self.counter_min <= value <= self.counter_max):
            counters = self._get_counters_data(manager)
            counters[str(item_id)] = value
            self._set_counters_data(manager, counters)
            await self.on_counter_value_changed.process_event(
                event, self.managed(manager), manager
            )

    def is_checked(self, item_id: T, manager: DialogManager) -> bool:
        """Проверить, выбран ли элемент (значение счетчика > 0)"""
        value = self.get_counter_value(item_id, manager)
        return value > 0

    def get_checked(self, manager: DialogManager) -> List[T]:
        """Получить список выбранных элементов (с положительным счетчиком)"""
        counters = self._get_counters_data(manager)
        return [self.type_factory(item_id) for item_id, value in counters.items()
                if value > 0]

    async def reset_checked(self, event: ChatEvent, manager: DialogManager) -> None:
        """Сбросить все счетчики"""
        self._set_counters_data(manager, {})

    async def set_checked(
            self,
            event: ChatEvent,
            item_id: T,
            checked: bool,
            manager: DialogManager,
    ) -> None:
        """Установить/снять выбор элемента"""
        item_id_str = str(item_id)
        counters = self._get_counters_data(manager)

        current_value = counters.get(item_id_str, self.counter_default)
        changed = False
        new_value = current_value

        if checked and current_value <= 0:
            # Если выбираем и счетчик <= 0, устанавливаем минимальное положительное значение
            new_value = max(self.counter_min, self.counter_increment, 1)
            if new_value <= self.counter_max:
                # Проверяем ограничение max_selected
                selected_count = sum(1 for v in counters.values() if v > 0)
                if self.max_selected == 0 or self.max_selected > selected_count:
                    counters[item_id_str] = new_value
                    changed = True
        elif not checked and current_value > 0:
            # Если снимаем выбор
            selected_count = sum(1 for v in counters.values() if v > 0)
            if selected_count > self.min_selected:
                counters[item_id_str] = 0
                changed = True

        if changed:
            self._set_counters_data(manager, counters)
            # Вызываем обработчики
            await self.on_counter_value_changed.process_event(
                event, self.managed(manager), manager
            )
            await self._process_on_state_changed(event, item_id_str, manager)

    async def _change_counter_value(
            self,
            callback: CallbackQuery,
            item_id: T,
            delta: float,
            manager: DialogManager,
    ):
        """Изменить значение счетчика"""
        item_id_str = str(item_id)
        current_value = self.get_counter_value(item_id, manager)

        if current_value == 0:
            # Если счетчик равен 0, просто применяем delta
            new_value = current_value + delta
            if new_value < self.counter_min:
                new_value = self.counter_min
            if new_value > self.counter_max:
                new_value = self.counter_max
        else:
            # Если счетчик > 0, применяем логику cycle
            new_value = current_value + delta

            if new_value < self.counter_min:
                if self.counter_cycle:
                    new_value = self.counter_max
                else:
                    new_value = self.counter_min
            elif new_value > self.counter_max:
                if self.counter_cycle:
                    new_value = self.counter_min
                else:
                    new_value = self.counter_max

        # Проверяем, что значение допустимо
        if new_value == 0 or (self.counter_min <= new_value <= self.counter_max):
            # Проверяем ограничения min_selected и max_selected при изменении состояния
            old_selected = current_value > 0
            new_selected = new_value > 0

            if old_selected != new_selected:
                counters = self._get_counters_data(manager)
                selected_count = sum(1 for v in counters.values() if v > 0)

                if new_selected:  # Становится выбранным
                    if self.max_selected > 0 and selected_count >= self.max_selected:
                        return
                else:  # Перестает быть выбранным
                    if selected_count <= self.min_selected:
                        return

            await self.set_counter_value(callback, item_id, new_value, manager)

            # Если состояние изменилось, вызываем обработчик состояния
            if old_selected != new_selected:
                await self._process_on_state_changed(callback, item_id_str, manager)

    async def _render_keyboard(
            self,
            data: dict,
            manager: DialogManager,
    ) -> RawKeyboard:
        keyboard = []
        items = self.items_getter(data)

        for pos, item in enumerate(items):
            item_data = {
                "data": data,
                "item": item,
                "pos": pos + 1,
                "pos0": pos,
            }
            item_id = str(self.item_id_getter(item))

            # Текст для кнопки выбора
            checked = self.is_checked(item_id, manager)
            text = self.checked_text if checked else self.unchecked_text
            choice_text = await text.render_text(item_data, manager)

            # Значение счетчика
            counter_value = self.get_counter_value(item_id, manager)

            # --- ПЕРВЫЙ РЯД: кнопка выбора (широкая) ---
            row1 = [
                InlineKeyboardButton(
                    text=choice_text,
                    callback_data=self._item_callback_data(f"choice:{item_id}"),
                )
            ]
            keyboard.append(row1)

            # --- ВТОРОЙ РЯД: кнопки счетчика (минус, значение, плюс) ---
            row2 = []

            # Кнопка минус (если включена)
            if self.counter_minus:
                minus_text = await self.counter_minus.render_text(item_data, manager)
                row2.append(InlineKeyboardButton(
                    text=minus_text,
                    callback_data=self._item_callback_data(f"minus:{item_id}"),
                ))

            # Кнопка со значением счетчика (если включена)
            if self.counter_text:
                counter_data = {**item_data, "value": counter_value}
                value_text = await self.counter_text.render_text(counter_data, manager)
                row2.append(InlineKeyboardButton(
                    text=value_text,
                    callback_data=self._item_callback_data(f"value:{item_id}"),
                ))

            # Кнопка плюс (если включена)
            if self.counter_plus:
                plus_text = await self.counter_plus.render_text(item_data, manager)
                row2.append(InlineKeyboardButton(
                    text=plus_text,
                    callback_data=self._item_callback_data(f"plus:{item_id}"),
                ))

            # Добавляем второй ряд только если есть кнопки счетчика
            if row2:
                keyboard.append(row2)

            # --- Опционально: добавляем пустую строку-разделитель между элементами ---
            # keyboard.append([])

        return keyboard

    async def _process_item_callback(
            self,
            callback: CallbackQuery,
            data: str,
            dialog: DialogProtocol,
            manager: DialogManager,
    ) -> bool:
        # Парсим тип действия и item_id
        if ":" in data:
            action_type, item_id_str = data.split(":", 1)
        else:
            # Для обратной совместимости, если данные пришли без типа
            action_type = "choice"
            item_id_str = data

        item_id = self.type_factory(item_id_str)

        if action_type == "choice":
            # Вызываем родительский метод для обработки клика
            return await super()._process_item_callback(callback, item_id_str, dialog, manager)
        elif action_type == "minus":
            # Уменьшение счетчика
            await self.on_counter_click.process_event(
                callback, self.managed(manager), manager
            )
            await self._change_counter_value(
                callback, item_id, -self.counter_increment, manager
            )
        elif action_type == "plus":
            # Увеличение счетчика
            await self.on_counter_click.process_event(
                callback, self.managed(manager), manager
            )
            await self._change_counter_value(
                callback, item_id, self.counter_increment, manager
            )
        elif action_type == "value":
            # Клик по значению счетчика
            await self.on_counter_text_click.process_event(
                callback, self.managed(manager), manager
            )
        else:
            return False

        return True

    async def _on_click(
            self,
            callback: CallbackQuery,
            select: ManagedWidget,
            manager: DialogManager,
            item_id: str,
    ):
        """Обработка клика по кнопке выбора"""
        checked = self.is_checked(item_id, manager)
        await self.set_checked(
            callback, item_id, not checked, manager
        )

    def managed(self, manager: DialogManager) -> "ManagedMultiSelectCounter[T]":
        return ManagedMultiSelectCounter(self, manager)


class ManagedMultiSelectCounter(ManagedWidget[MultiSelectCounter[T]], Generic[T]):
    """Управляемый класс для MultiSelectCounter"""

    def is_checked(self, item_id: T) -> bool:
        """Проверить, выбран ли элемент"""
        return self.widget.is_checked(item_id, self.manager)

    def get_checked(self) -> List[T]:
        """Получить список выбранных элементов"""
        return self.widget.get_checked(self.manager)

    def get_counter_value(self, item_id: T) -> float:
        """Получить значение счетчика для элемента"""
        return self.widget.get_counter_value(item_id, self.manager)

    async def set_counter_value(self, item_id: T, value: float) -> None:
        """Установить значение счетчика для элемента"""
        await self.widget.set_counter_value(
            self.manager.event, item_id, value, self.manager
        )

    async def set_checked(self, item_id: T, checked: bool) -> None:
        """Установить/снять выбор элемента"""
        await self.widget.set_checked(
            self.manager.event, item_id, checked, self.manager
        )

    async def reset_checked(self) -> None:
        """Сбросить все счетчики"""
        await self.widget.reset_checked(self.manager.event, self.manager)

    def get_counters_data(self) -> Dict[str, float]:
        """Получить все данные счетчиков"""
        return self.widget._get_counters_data(self.manager)
