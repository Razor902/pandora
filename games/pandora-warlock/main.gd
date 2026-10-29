extends Control
# Pandora Warlock — Tactical Chess, Series 1 Cards (v1).
# Single-player: guard the lighthouse through 8 rounds against the Shades.
# Rules (see DESIGN.md):
# - Lighthouse 20 HP. Lose at 0. Win by standing after round 8.
# - Starlight starts at 4, +2 each new round. Deploying a warlock costs starlight.
# - Hand starts at 3 cards from an 8-card deck; draw 1 each new round.
# - Constellations are lanes. Polaris heals its warlock 1 HP at round start.
#   Orion gives its warlock +1 BP when striking.
# - A Shade in a guarded lane fights the warlock. A Shade in an unguarded
#   lane advances; reaching the lighthouse costs its BP in lighthouse HP.

var lighthouse_hp := 20
var lighthouse_max := 20
var round_num := 1
var max_rounds := 8
var starlight := 4
var deck: Array = []
var hand: Array = []
var lanes: Array = []
var selected_card := -1
var game_over := false
var game_won := false
var log_lines: Array = []
var title_tap_count := 0
var eggs_found: Array = []
# Texture-swap Easter egg (own implementation of the paired-texture idea:
# two emblems with paired colours; one is swapped each new game).
# In an art pass these colour emblems become TextureRects with paired
# textures — the swap check below stays the same.
var anomaly_lane := -1
var anomaly_found := false
var emblem_buttons: Array = []

var status_label: Label
var secrets_label: Label
var result_label: Label
var log_label: Label
var lane_ui: Array = []
var hand_buttons: Array = []
var end_button: Button
var restart_button: Button


func _ready() -> void:
	randomize()
	_build_ui()
	start_game()


func _build_ui() -> void:
	var root := VBoxContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_theme_constant_override("separation", 10)
	add_child(root)

	var title_button := Button.new()
	title_button.text = "Pandora Warlock"
	title_button.flat = true
	title_button.pressed.connect(_on_title_pressed)
	root.add_child(title_button)
	var subtitle := Label.new()
	subtitle.text = "Tactical Chess — Series 1 Cards"
	root.add_child(subtitle)

	status_label = Label.new()
	status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(status_label)

	secrets_label = Label.new()
	root.add_child(secrets_label)

	var emblems_label := Label.new()
	emblems_label.text = "Constellation emblems"
	root.add_child(emblems_label)
	var emblems_box := HBoxContainer.new()
	root.add_child(emblems_box)
	for i in range(2):
		var emblem_button := Button.new()
		emblem_button.custom_minimum_size = Vector2(0, 52)
		emblem_button.pressed.connect(_on_emblem_pressed.bind(i))
		emblems_box.add_child(emblem_button)
		emblem_buttons.append(emblem_button)

	result_label = Label.new()
	result_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(result_label)

	var lane_defs := [
		{"name": "Polaris", "title": "TRUE NORTH", "bonus": "Warlocks here heal 1 HP at the start of each round."},
		{"name": "Orion", "title": "THE HUNTER", "bonus": "Warlocks here strike with +1 BP."},
	]
	for i in range(lane_defs.size()):
		var defs: Dictionary = lane_defs[i]
		var panel := PanelContainer.new()
		var box := VBoxContainer.new()
		box.add_theme_constant_override("separation", 4)
		panel.add_child(box)
		root.add_child(panel)
		var name_label := Label.new()
		name_label.text = "%s — %s" % [defs["name"], defs["title"]]
		box.add_child(name_label)
		var bonus_label := Label.new()
		bonus_label.text = defs["bonus"]
		bonus_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(bonus_label)
		var warlock_label := Label.new()
		warlock_label.text = "Open slot"
		box.add_child(warlock_label)
		var shade_label := Label.new()
		shade_label.text = "Sky is clear"
		box.add_child(shade_label)
		var buttons := HBoxContainer.new()
		box.add_child(buttons)
		var deploy_button := Button.new()
		deploy_button.text = "Deploy here"
		deploy_button.custom_minimum_size = Vector2(0, 52)
		deploy_button.pressed.connect(_on_deploy_pressed.bind(i))
		buttons.add_child(deploy_button)
		var strike_button := Button.new()
		strike_button.text = "Strike"
		strike_button.custom_minimum_size = Vector2(0, 52)
		strike_button.pressed.connect(_on_strike_pressed.bind(i))
		buttons.add_child(strike_button)
		lane_ui.append({
			"warlock_label": warlock_label,
			"shade_label": shade_label,
			"deploy_button": deploy_button,
			"strike_button": strike_button,
		})

	var hand_label := Label.new()
	hand_label.text = "Your hand — tap a card, then Deploy here on a constellation."
	root.add_child(hand_label)
	var hand_box := VBoxContainer.new()
	hand_box.add_theme_constant_override("separation", 4)
	root.add_child(hand_box)
	for i in range(8):
		var button := Button.new()
		button.custom_minimum_size = Vector2(0, 52)
		button.pressed.connect(_on_card_selected.bind(i))
		hand_box.add_child(button)
		hand_buttons.append(button)

	end_button = Button.new()
	end_button.text = "End round"
	end_button.custom_minimum_size = Vector2(0, 56)
	end_button.pressed.connect(_on_end_round_pressed)
	root.add_child(end_button)

	restart_button = Button.new()
	restart_button.text = "Play again"
	restart_button.custom_minimum_size = Vector2(0, 56)
	restart_button.pressed.connect(_on_restart_pressed)
	root.add_child(restart_button)

	log_label = Label.new()
	log_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(log_label)

	var help := Label.new()
	help.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	help.text = "How to play: deploy warlocks to guard constellations, strike Shades in their lane, then end the round. Shades in an unguarded lane creep closer — if one reaches an unguarded constellation, it hits the lighthouse. Hold all 8 rounds. Rumor says the table hides secrets."
	root.add_child(help)


func _card_defs() -> Array:
	return [
		{"name": "Ember Warlock", "cost": 2, "hp": 5, "bp": 3},
		{"name": "Tide Warlock", "cost": 2, "hp": 6, "bp": 2},
		{"name": "Thorn Warlock", "cost": 1, "hp": 3, "bp": 2},
		{"name": "Storm Warlock", "cost": 3, "hp": 4, "bp": 4},
		{"name": "Dawn Warlock", "cost": 2, "hp": 4, "bp": 3},
		{"name": "Night Warlock", "cost": 3, "hp": 7, "bp": 2},
		{"name": "Stone Warlock", "cost": 1, "hp": 6, "bp": 1},
		{"name": "Wild Warlock", "cost": 2, "hp": 5, "bp": 2},
	]


func _make_shade(name: String, hp: int, bp: int) -> Dictionary:
	return {"name": name, "hp": hp, "max_hp": hp, "bp": bp, "steps": 2}


func _shade_for_round(r: int) -> Dictionary:
	if r <= 3:
		return _make_shade("Shade Wisp", 3, 2)
	if r <= 5:
		if randi() % 2 == 0:
			return _make_shade("Shade Wisp", 3, 2)
		return _make_shade("Shade Hound", 5, 3)
	if r <= 7:
		if randi() % 2 == 0:
			return _make_shade("Shade Hound", 5, 3)
		return _make_shade("Shade Brute", 8, 4)
	return _make_shade("Shade Brute", 8, 4)


func start_game() -> void:
	lighthouse_hp = lighthouse_max
	round_num = 1
	starlight = 4
	deck = []
	for card in _card_defs():
		deck.append((card as Dictionary).duplicate(true))
	deck.shuffle()
	hand = []
	for _i in range(3):
		_draw_card()
	lanes = [
		{"name": "Polaris", "warlock": null, "shade": null},
		{"name": "Orion", "warlock": null, "shade": null},
	]
	selected_card = -1
	game_over = false
	game_won = false
	# Pick the swapped emblem for this game: 0 = Polaris, 1 = Orion.
	anomaly_lane = randi() % 2
	anomaly_found = false
	log_lines = ["The lighthouse stands at 20. Round 1 of 8. The sky is clear."]
	refresh_ui()


func _draw_card() -> void:
	if not deck.is_empty():
		hand.append(deck.pop_back())


func _log(message: String) -> void:
	log_lines.append(message)
	while log_lines.size() > 8:
		log_lines.remove_at(0)


# Easter eggs (see DESIGN.md for the dev list — players find these in play).
func _found_egg(egg_id: String, line: String) -> void:
	if eggs_found.has(egg_id):
		return
	eggs_found.append(egg_id)
	_log("★ Secret found: " + line)


func _on_title_pressed() -> void:
	title_tap_count += 1
	if title_tap_count == 3:
		_found_egg("twin_thrones", "The twin thrones watch over this table.")
		refresh_ui()


func _refresh_emblems() -> void:
	# Paired emblem colours: Polaris gold, Orion steel. When the swap is
	# live, the swapped emblem wears the other emblem's colour. Once the
	# swap is found, both emblems return to their own colours.
	var polaris_gold := Color(1, 0.75, 0.2)
	var orion_steel := Color(0.4, 0.6, 1.0)
	if emblem_buttons.size() < 2:
		return
	var polaris_button: Button = emblem_buttons[0]
	var orion_button: Button = emblem_buttons[1]
	polaris_button.text = "Polaris emblem"
	orion_button.text = "Orion emblem"
	if anomaly_found or anomaly_lane < 0:
		polaris_button.modulate = polaris_gold
		orion_button.modulate = orion_steel
	elif anomaly_lane == 0:
		polaris_button.modulate = orion_steel
		orion_button.modulate = orion_steel
	else:
		polaris_button.modulate = polaris_gold
		orion_button.modulate = polaris_gold


func _on_emblem_pressed(lane_idx: int) -> void:
	if game_over or anomaly_found:
		return
	if lane_idx == anomaly_lane:
		anomaly_found = true
		_found_egg("wrong_detail", "The wrong detail — one emblem wore the other's colour.")
		refresh_ui()


func refresh_ui() -> void:
	status_label.text = "Lighthouse %d/20  •  Round %d/8  •  Starlight %d  •  Deck %d  •  Hand %d" % [lighthouse_hp, round_num, starlight, deck.size(), hand.size()]
	secrets_label.text = "Secrets found: %d/5" % eggs_found.size()
	_refresh_emblems()
	if game_over:
		if game_won:
			result_label.text = "Victory — the lighthouse stood all 8 rounds."
		else:
			result_label.text = "The lighthouse has fallen."
		result_label.visible = true
	else:
		result_label.text = ""
		result_label.visible = false
	log_label.text = "\n".join(log_lines)
	for i in range(lanes.size()):
		var lane: Dictionary = lanes[i]
		var ui: Dictionary = lane_ui[i]
		var warlock_label: Label = ui["warlock_label"]
		var shade_label: Label = ui["shade_label"]
		var deploy_button: Button = ui["deploy_button"]
		var strike_button: Button = ui["strike_button"]
		if lane["warlock"] != null:
			var w: Dictionary = lane["warlock"]
			warlock_label.text = "%s — %d HP / %d BP" % [w["name"], w["hp"], w["bp"]]
		else:
			warlock_label.text = "Open slot"
		if lane["shade"] != null:
			var s: Dictionary = lane["shade"]
			shade_label.text = "%s — %d HP / %d BP — %d steps away" % [s["name"], s["hp"], s["bp"], s["steps"]]
		else:
			shade_label.text = "Sky is clear"
		var can_deploy := (not game_over and selected_card >= 0 and lane["warlock"] == null and (hand[selected_card] as Dictionary)["cost"] <= starlight)
		deploy_button.disabled = not can_deploy
		var can_strike := (not game_over and lane["warlock"] != null and lane["shade"] != null and not (lane["warlock"] as Dictionary)["struck"])
		strike_button.disabled = not can_strike
	for i in range(hand_buttons.size()):
		var button: Button = hand_buttons[i]
		if i < hand.size():
			var card: Dictionary = hand[i]
			var marker := ""
			if i == selected_card:
				marker = "  ◀ selected"
			button.text = "%s — %d starlight, %d HP, %d BP%s" % [card["name"], card["cost"], card["hp"], card["bp"], marker]
			button.visible = true
			button.disabled = game_over or card["cost"] > starlight
		else:
			button.visible = false
	end_button.disabled = game_over
	restart_button.visible = game_over


func _on_card_selected(index: int) -> void:
	if game_over or index >= hand.size():
		return
	if selected_card == index:
		selected_card = -1
	else:
		selected_card = index
	refresh_ui()


func _on_deploy_pressed(lane_idx: int) -> void:
	if game_over or selected_card < 0 or selected_card >= hand.size():
		return
	var lane: Dictionary = lanes[lane_idx]
	if lane["warlock"] != null:
		return
	var card: Dictionary = hand[selected_card]
	if card["cost"] > starlight:
		return
	starlight -= int(card["cost"])
	var warlock := {
		"name": card["name"],
		"cost": card["cost"],
		"hp": card["hp"],
		"max_hp": card["hp"],
		"bp": card["bp"],
		"struck": false,
	}
	lane["warlock"] = warlock
	hand.remove_at(selected_card)
	selected_card = -1
	_log("Deployed %s to %s." % [warlock["name"], lane["name"]])
	if warlock["name"] == "Stone Warlock" and lane_idx == 1:
		_found_egg("stone_remembers", "The stone remembers the first wall.")
	if warlock["name"] == "Night Warlock" and lane_idx == 0:
		_found_egg("night_shift", "The night shift keeps watch.")
	refresh_ui()


func _on_strike_pressed(lane_idx: int) -> void:
	if game_over:
		return
	var lane: Dictionary = lanes[lane_idx]
	if lane["warlock"] == null or lane["shade"] == null:
		return
	var warlock: Dictionary = lane["warlock"]
	if warlock["struck"]:
		return
	var shade: Dictionary = lane["shade"]
	var damage: int = int(warlock["bp"]) + (1 if lane_idx == 1 else 0)
	shade["hp"] -= damage
	warlock["struck"] = true
	_log("%s strikes %s for %d BP." % [warlock["name"], shade["name"], damage])
	if shade["hp"] <= 0:
		lane["shade"] = null
		_log("%s fades into the dark." % shade["name"])
	refresh_ui()


func _spawn_shade() -> void:
	var free_lanes: Array = []
	for i in range(lanes.size()):
		if lanes[i]["shade"] == null:
			free_lanes.append(i)
	if free_lanes.is_empty():
		_log("No Shade stirs — every lane is already haunted.")
		return
	var lane_idx: int = free_lanes[randi() % free_lanes.size()]
	var shade := _shade_for_round(round_num)
	lanes[lane_idx]["shade"] = shade
	_log("A %s gathers over %s." % [shade["name"], lanes[lane_idx]["name"]])


func _on_end_round_pressed() -> void:
	if game_over:
		return
	var polaris: Dictionary = lanes[0]
	if polaris["warlock"] != null:
		var w: Dictionary = polaris["warlock"]
		if int(w["hp"]) < int(w["max_hp"]):
			w["hp"] = mini(int(w["max_hp"]), int(w["hp"]) + 1)
			_log("Polaris mends %s (+1 HP)." % w["name"])
	for lane_idx in range(lanes.size()):
		var lane: Dictionary = lanes[lane_idx]
		if lane["shade"] == null:
			continue
		var shade: Dictionary = lane["shade"]
		if lane["warlock"] != null:
			var guard_warlock: Dictionary = lane["warlock"]
			var damage: int = int(guard_warlock["bp"]) + (1 if lane_idx == 1 else 0)
			shade["hp"] -= damage
			_log("%s holds the lane, striking %s for %d BP." % [guard_warlock["name"], shade["name"], damage])
			if shade["hp"] <= 0:
				lane["shade"] = null
				_log("%s fades into the dark." % shade["name"])
			else:
				guard_warlock["hp"] -= int(shade["bp"])
				_log("%s hits back for %d BP." % [shade["name"], shade["bp"]])
				if guard_warlock["hp"] <= 0:
					lane["warlock"] = null
					_log("%s falls." % guard_warlock["name"])
		else:
			shade["steps"] -= 1
			if int(shade["steps"]) <= 0:
				lighthouse_hp -= int(shade["bp"])
				lane["shade"] = null
				_log("%s reaches the lighthouse! -%d HP." % [shade["name"], shade["bp"]])
			else:
				_log("%s creeps closer (%d steps away)." % [shade["name"], shade["steps"]])
	if lighthouse_hp <= 0:
		lighthouse_hp = 0
		game_over = true
		game_won = false
		_log("The lighthouse has fallen.")
		refresh_ui()
		return
	round_num += 1
	if round_num > max_rounds:
		game_over = true
		game_won = true
		if lighthouse_hp == lighthouse_max:
			_found_egg("perfect_light", "Perfect Light — the lighthouse never dimmed.")
		_log("Eight rounds held. The lighthouse still stands.")
		refresh_ui()
		return
	starlight += 2
	_draw_card()
	_spawn_shade()
	for lane in lanes:
		if lane["warlock"] != null:
			(lane["warlock"] as Dictionary)["struck"] = false
	selected_card = -1
	_log("Round %d of 8 begins. +2 starlight." % round_num)
	refresh_ui()


func _on_restart_pressed() -> void:
	start_game()
