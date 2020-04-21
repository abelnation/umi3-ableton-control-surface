##################################################################
#
#   Copyright (C) 2012 Imaginando, Lda & Teenage Engineering AB
#
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   For more information about this license please consult the
#   following webpage: http://www.gnu.org/licenses/gpl-2.0.html
#
##################################################################

# Logidy UMI3 Python Scripts V0.0.1 (Abel custom)
# Customization by: Abel Allison

from functools import partial
import time

import Live


# Ableton Live Framework imports
from _Framework.ButtonElement import ButtonElement
from _Framework.ControlSurface import ControlSurface
from _Framework.EncoderElement import EncoderElement
from _Framework.MixerComponent import MixerComponent
from _Framework.SessionComponent import SessionComponent
from _Framework.TransportComponent import TransportComponent

# Provides many constants
from _Framework.InputControlElement import *

# Utils from APC libs
from _APC import ControlElementUtils as APCUtils
from _APC.DetailViewCntrlComponent import DetailViewCntrlComponent

from .consts import *
from .util import color_to_bytes
from .util import midi_bytes_to_values

STATE_OFF = 0.0
STATE_ON = 1.0

LOOPER_DEVICE_CLASS = 'Looper'
LOOPER_STATE_PARAM_NAME = 'Device On'

#
# Logidy UMI3 Internal Implementation Constants
#

class UMI3(ControlSurface):
	def __init__(self, *args, **kwargs):
		ControlSurface.__init__(self, *args, **kwargs)

		self.log_message('__init__()')

		with self.component_guard():
			self._build_components()

		self.show_message("Version: " + VERSION)


	#
	# Ableton Helpers
	#

	@property
	def num_tracks(self):
		return min(NUM_TRACKS, len(self.song().tracks))

	@property
	def num_scenes(self):
		return min(NUM_SCENES, len(self.song().scenes))

	@property
	def selected_track(self):
		return self.song().view.selected_track

	@property
	def selected_track_num(self):
		return list(self.song().tracks).index(self.selected_track)

	@property
	def selected_scene(self):
		return self.song().view.selected_scene

	@property
	def selected_scene_num(self):
		return list(self.song().scenes).index(self.selected_scene)

	@property
	def selected_clip_slot(self):
		return self.selected_track.clip_slots[self.selected_scene_num]

	def get_selected_track_devices(self, class_name):
		return [
			device for device in self.selected_track.devices
			if device.class_name == class_name
		]
	#
	# Connected Components
	#

	def _build_components(self):
		# UMI3 Buttons
		self._button_umi3_1 = APCUtils.make_button(UMI3_CHANNEL, UMI3_1)
		self._button_umi3_1.add_value_listener(self.debug_button_handler)

		self._button_umi3_2 = APCUtils.make_button(UMI3_CHANNEL, UMI3_2)
		self._button_umi3_2.add_value_listener(self.debug_button_handler)

		self._button_umi3_3 = APCUtils.make_button(UMI3_CHANNEL, UMI3_3)
		self._button_umi3_3.add_value_listener(self.debug_button_handler)

		self._all_buttons = [self._button_umi3_1, self._button_umi3_2, self._button_umi3_3]

		self.map_looper_controls_for_current_track()

		self.song().view.add_selected_track_listener(self.selected_track_changed)

	#
	# Mixer Control Mapping
	#

	def selected_track_changed(self):
		self.log_message('selected_track_changed()')
		self.map_looper_controls_for_current_track()

	def map_looper_controls_for_current_track(self):
		self.log_message('map_looper_controls_for_current_track()')
		# self._toggle_loopers_for_selected_track()
		self._map_buttons_to_channel_for_selected_track()

	def _map_buttons_to_channel_for_selected_track(self):
		selected_track_num = self.selected_track_num
		new_channel_num = selected_track_num + 1
		self.log_message('Mapping buttons to channel %s' % new_channel_num)

		with self.component_guard():
			for button in self._all_buttons:
				button.use_default_message()
				button.set_channel(new_channel_num)

		self.request_rebuild_midi_map()

	def _toggle_loopers_for_selected_track(self):
		# 1. Disable existing loopers
		for track in self.song().tracks:
			for device in [d for d in track.devices if d.class_name == 'Looper']:
				param = [p for p in device.parameters if p.name == 'Device On'][0]
				param.value = STATE_OFF

		# Map loopers for current track
		selected_track = self.selected_track
		for device in [d for d in selected_track.devices if d.class_name == 'Looper']:
			param = [p for p in device.parameters if p.name == 'Device On'][0]
			param.value = STATE_ON

	#
	# Refresh handling
	#

	def handle_sysex(self, midi_bytes):
		super(UMI3, self).handle_sysex(midi_bytes)
		self.log_message("sysex: %s" % (midi_bytes, ))

	def refresh_state(self):
		super(UMI3, self).refresh_state()

		self.log_message("refresh_state()")
		self.retries_count = 0
		self.device_connected = False

		self.map_looper_controls_for_current_track()

	#
	# Connection Management
	#

	def update(self):
		super(UMI3, self).update()
		self.log_message('update()')

	def build_midi_map(self, midi_map_handle):
		super(UMI3, self).build_midi_map(midi_map_handle)
		self.log_message('build_midi_map()')

		# map mixer controls to currently selected track
		# self.map_looper_controls_for_current_track()

	def suggest_input_port(self):
		return "UMI3 Midi Device"

	def suggest_output_port(self):
		return "UMI3 Midi Device"

	#
	# Debug utils
	#

	def param_value_updated(self, param):
		self.log_message('Param update: %s(%s)' % (param.name, param.value))
		self.log_message('    value_items: %s' % (list(param.value_items), ))

	def debug_button_handler(self, value, *args, **kwargs):
		self.log_message('button: %s' % value)

	def debug_note_handler(self, value, *args, **kwargs):
		self.log_message('note: %s' % value)

	def handle_nonsysex(self, midi_bytes):
		super(UMI3, self).handle_nonsysex(midi_bytes)
		channel, identifier, value, is_pitchbend = midi_bytes_to_values(midi_bytes)
		if not is_pitchbend:
			self.log_message('midi ch:%s value:%s(%s)' % (channel, identifier, value))

