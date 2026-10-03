# Extracted input helpers; see IMPORT-MANIFEST.json and LICENSE.upstream.txt.
# Reference only: unintegrated and not engine-tested.
extends SceneTree

func _inject_input(step: Dictionary) -> void:
	var via := String(step.get("via", ""))
	var held := int(step.get("held_ms", 60))
	if via.begins_with("pad_"):
		var je := InputEventJoypadButton.new()
		je.button_index = JOY_BUTTON_A
		je.pressed = true
		Input.parse_input_event(je)
	elif via.begins_with("stick_"):
		var jm := InputEventJoypadMotion.new()
		jm.axis = JOY_AXIS_LEFT_X
		jm.axis_value = -1.0
		Input.parse_input_event(jm)
	var ev_press: InputEventKey = null
	var key_via := via if not via.begins_with("pad_") and not via.begins_with("stick_") else ""
	var code := _key_for(key_via if key_via != "" else String(step.get("action", "")))
	if code != KEY_NONE:
		ev_press = InputEventKey.new()
		ev_press.physical_keycode = code
		ev_press.keycode = code
		ev_press.pressed = true
		Input.parse_input_event(ev_press)
	var ticks := int(held / 1000.0 * Engine.get_physics_ticks_per_second())
	for i in ticks:
		await physics_frame
	if ev_press != null:
		var ev_rel := ev_press.duplicate()
		ev_rel.pressed = false
		Input.parse_input_event(ev_rel)
	if via.begins_with("pad_"):
		var jr := InputEventJoypadButton.new()
		jr.button_index = JOY_BUTTON_A
		jr.pressed = false
		Input.parse_input_event(jr)
	elif via.begins_with("stick_"):
		var jmr := InputEventJoypadMotion.new()
		jmr.axis = JOY_AXIS_LEFT_X
		jmr.axis_value = 0.0
		Input.parse_input_event(jmr)
	await physics_frame

func _key_for(name: String) -> Key:
	match name:
		"push", "key_w": return KEY_W
		"steer_left", "key_a": return KEY_A
		"steer_right", "key_d": return KEY_D
		"ollie", "key_space": return KEY_SPACE
		"bail_force", "key_b": return KEY_B
		"correct_hold", "key_d": return KEY_D
		"any_key", "key_space": return KEY_SPACE
		"ui_accept", "key_enter": return KEY_ENTER
		_: return KEY_NONE
