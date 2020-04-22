import time

from _Framework.ComboElement import EventElement, WrapperElement
from _Framework.Util import lazy_attribute

from _Framework import Task

# WAITING <-----------------------------------------------+<------------+
# |                                                       ^             |
# button_down (ignore button_up                           |             |
# |                                                       |             |
# V                                                       |             |
# FIRST_BUTTON_DOWN ---> long_tap_delay_passes --> NOTIFY_LONG_TAP      |
# |                                                                     |
# button_up                                                             |
# |                                                                     |
# V                                                                     |
# MAYBE_DOUBLE_TAP ---> double_tap_delay_passes --> NOTIFY_SINGLE_TAP --+
# |
# button_down
# |
# V
# NOTIFY_DOUBLE_TAP --> ... (back to WAITING)
#

BUTTON_OFF = 0


class MultiButton(WrapperElement):
    u"""
    Element wrapper that provides a facade with three events:
    - single_press
    - double_press
    - long_press
    """

    __subject_events__ = (u'single_press', u'double_press', u'long_press')

    DOUBLE_PRESS_MAX_DELAY = 0.2
    LONG_TAP_MAX_DELAY = 0.75

    def __init__(self, wrapped_control=None, *a, **k):
        super(MultiButton, self).__init__(wrapped_control=wrapped_control, *a, **k)
        self.register_wrapped()
        self.request_listen_nested_control_elements()

        self._current_task = None

        self._long_press_task = self._tasks.add(Task.sequence(
            Task.wait(self.LONG_TAP_MAX_DELAY),
            Task.run(self.notify_long_press)
        )).kill()

        self._double_press_task = self._tasks.add(Task.sequence(
            Task.wait(self.DOUBLE_PRESS_MAX_DELAY),
            Task.run(self.notify_single_press)
        )).kill()

    def on_nested_control_element_value(self, value, control):

        print('on_nested_control_element_value (time: %s)' % time.time())

        button_down = (not control.is_momentary() or value)
        button_up = not button_down

        waiting_for_long_tap = not self._long_press_task.is_killed
        waiting_for_double_tap = not self._double_press_task.is_killed

        # Waiting for first activity
        if not (waiting_for_long_tap or waiting_for_double_tap):
            if button_down:
                self._long_press_task.restart()
            return

        # We have a long-tap candidate
        if waiting_for_long_tap and button_up:
            # Button released before it was a long-tap
            self._long_press_task.kill()
            self._double_press_task.restart()
            return

        if waiting_for_double_tap and button_down:
            self._double_press_task.kill()
            self.notify_double_press()

        super(MultiButton, self).on_nested_control_element_value(value, control)

    @lazy_attribute
    def single_press(self):
        return EventElement(self, 'single_press')

    @lazy_attribute
    def double_press(self):
        return EventElement(self, 'double_press')

    @lazy_attribute
    def long_press(self):
        return EventElement(self, 'long_press')
