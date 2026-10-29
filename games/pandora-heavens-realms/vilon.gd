extends Node2D
# Pandora Heavens Realms — Vilon, playable, v1.03, 2026-10-28.
# First playable realm. Curtis names the lands, Wren and Rebecka lay the lands and cattle.
# Vilon, 1st layer: safari animals in realism, rainforest too, wetlands below.
# Cattle, first and foremost: Ox first, bison next — the bison greeting only counts
# after the ox greeting. No real fingerprint data is collected or stored here.
# Controls: drag on touch to walk toward your finger, or WASD / arrow keys.
# Goal: greet the Ox, then the Bison, then cross the veil gate at the top of the map.

const WORLD_W = 1440.0
const WORLD_H = 1920.0
const WALK_SPEED = 230.0

var player: CharacterBody2D
var ox: Node2D
var bison: Node2D
var boat: Node2D
var quest_label: Label
var eggs_label: Label
var toast_label: Label
var toast_timer: Timer
var touch_target: Vector2 = Vector2.INF
var ox_greeted = false
var bison_greeted = false
var vilon_done = false
var eggs_found = 0
var egg_feather_done = false
var egg_clearing_done = false
var egg_plank_done = false
var wander_timer = 0.0
var ox_dir = Vector2.ZERO
var bison_dir = Vector2.ZERO
var boat_dir = 1.0

func _ready():
	_build_ground()
	_build_player()
	_build_animals()
	_build_boat()
	_build_hud()
	var cam = Camera2D.new()
	cam.position_smoothing_enabled = true
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = int(WORLD_W)
	cam.limit_bottom = int(WORLD_H)
	player.add_child(cam)
	cam.make_current()
	_update_quest()

func _build_ground():
	var base = ColorRect.new()
	base.color = Color(0.45, 0.55, 0.25)
	base.position = Vector2(0, 0)
	base.size = Vector2(WORLD_W, WORLD_H)
	add_child(base)
	# Rainforest: dense green, right side.
	var forest = ColorRect.new()
	forest.color = Color(0.10, 0.35, 0.15)
	forest.position = Vector2(950, 250)
	forest.size = Vector2(490, 1000)
	add_child(forest)
	_forest_label("RAINFOREST", Vector2(1050, 300))
	# Wetlands water: low water lands across the bottom.
	var water = ColorRect.new()
	water.color = Color(0.15, 0.45, 0.65)
	water.position = Vector2(0, 1500)
	water.size = Vector2(WORLD_W, 420)
	add_child(water)
	# Boardwalk: planks across the water, south to north.
	var walk = ColorRect.new()
	walk.color = Color(0.45, 0.30, 0.15)
	walk.position = Vector2(680, 1420)
	walk.size = Vector2(80, 500)
	add_child(walk)
	_forest_label("BOARDWALK", Vector2(640, 1460))
	_forest_label("WETLANDS — marsh, swamp, reeds", Vector2(60, 1540))
	_forest_label("SAFARI — realism, 1st layer", Vector2(60, 120))
	_forest_label("VILON — the veil is at the top", Vector2(480, 40))
	# Veil gate: gold band at the top center.
	var veil = ColorRect.new()
	veil.color = Color(0.90, 0.75, 0.25)
	veil.position = Vector2(620, 0)
	veil.size = Vector2(200, 60)
	add_child(veil)
	_forest_label("VEIL GATE", Vector2(645, 70))
	# Hidden egg spots are NOT labeled in the world; the HUD shows count only.
	var feather = ColorRect.new()
	feather.name = "Feather"
	feather.color = Color(0.95, 0.95, 0.90)
	feather.position = Vector2(150, 200)
	feather.size = Vector2(18, 8)
	add_child(feather)

func _forest_label(text: String, pos: Vector2):
	var l = Label.new()
	l.text = text
	l.position = pos
	l.add_theme_font_size_override("font_size", 30)
	add_child(l)

func _build_player():
	player = CharacterBody2D.new()
	player.position = Vector2(720, 1300)
	var body = ColorRect.new()
	body.color = Color(0.95, 0.70, 0.20)
	body.position = Vector2(-16, -16)
	body.size = Vector2(32, 32)
	player.add_child(body)
	var tag = Label.new()
	tag.text = "YOU"
	tag.position = Vector2(-22, -52)
	tag.add_theme_font_size_override("font_size", 26)
	player.add_child(tag)
	add_child(player)

func _build_animals():
	ox = _make_animal("OX", Color(0.55, 0.45, 0.35), Vector2(300, 700))
	bison = _make_animal("BISON", Color(0.30, 0.22, 0.15), Vector2(500, 1000))

func _make_animal(tag_text: String, col: Color, pos: Vector2) -> Node2D:
	var a = Node2D.new()
	a.position = pos
	var body = ColorRect.new()
	body.color = col
	body.position = Vector2(-30, -20)
	body.size = Vector2(60, 40)
	a.add_child(body)
	var tag = Label.new()
	tag.text = tag_text
	tag.position = Vector2(-32, -58)
	tag.add_theme_font_size_override("font_size", 28)
	a.add_child(tag)
	add_child(a)
	return a

func _build_boat():
	boat = Node2D.new()
	boat.position = Vector2(300, 1700)
	var hull = ColorRect.new()
	hull.color = Color(0.55, 0.35, 0.15)
	hull.position = Vector2(-60, -16)
	hull.size = Vector2(120, 32)
	boat.add_child(hull)
	var tag = Label.new()
	tag.text = "BOAT — step on to ride"
	tag.position = Vector2(-110, -56)
	tag.add_theme_font_size_override("font_size", 26)
	boat.add_child(tag)
	add_child(boat)

func _build_hud():
	var layer = CanvasLayer.new()
	add_child(layer)
	quest_label = Label.new()
	quest_label.position = Vector2(20, 20)
	quest_label.add_theme_font_size_override("font_size", 30)
	layer.add_child(quest_label)
	eggs_label = Label.new()
	eggs_label.position = Vector2(20, 64)
	eggs_label.add_theme_font_size_override("font_size", 30)
	layer.add_child(eggs_label)
	toast_label = Label.new()
	toast_label.position = Vector2(20, 108)
	toast_label.add_theme_font_size_override("font_size", 30)
	layer.add_child(toast_label)
	toast_timer = Timer.new()
	toast_timer.one_shot = true
	toast_timer.wait_time = 3.0
	toast_timer.timeout.connect(_on_toast_timeout)
	layer.add_child(toast_timer)
	var back = Button.new()
	back.text = "Back to Realms"
	back.position = Vector2(20, 1180)
	back.custom_minimum_size = Vector2(300, 80)
	back.pressed.connect(_on_back_pressed)
	layer.add_child(back)

func _on_toast_timeout():
	toast_label.text = ""

func _show_toast(text: String):
	toast_label.text = text
	toast_timer.start()

func _on_back_pressed():
	get_tree().change_scene_to_file("res://main.tscn")

func _update_quest():
	if vilon_done:
		quest_label.text = "Vilon walked! The veil is open."
	elif bison_greeted:
		quest_label.text = "Ox greeted, bison greeted — cross the veil gate."
	elif ox_greeted:
		quest_label.text = "Ox greeted — now greet the Bison."
	else:
		quest_label.text = "Greet the Ox first, then the Bison."
	eggs_label.text = "Eggs: " + str(eggs_found) + "/3"

func _unhandled_input(event):
	if event is InputEventScreenTouch and event.pressed:
		touch_target = _screen_to_world(event.position)
	elif event is InputEventScreenDrag:
		touch_target = _screen_to_world(event.position)
	elif event is InputEventMouseButton and event.pressed:
		touch_target = _screen_to_world(event.position)

func _screen_to_world(screen_pos: Vector2) -> Vector2:
	var cam = get_viewport().get_camera_2d()
	if cam == null:
		return screen_pos
	return screen_pos + cam.get_screen_center_position() - get_viewport_rect().size / 2.0

func _physics_process(delta):
	var move = Vector2.ZERO
	var keys = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if keys != Vector2.ZERO:
		move = keys.normalized()
		touch_target = Vector2.INF
	elif touch_target != Vector2.INF:
		var diff = touch_target - player.position
		if diff.length() < 12.0:
			touch_target = Vector2.INF
		else:
			move = diff.normalized()
	var speed = WALK_SPEED
	if _in_water(player.position) and not _on_boardwalk(player.position):
		speed = WALK_SPEED * 0.55
	elif _in_forest(player.position):
		speed = WALK_SPEED * 0.8
	player.velocity = move * speed
	player.move_and_slide()
	player.position.x = clamp(player.position.x, 16, WORLD_W - 16)
	player.position.y = clamp(player.position.y, 16, WORLD_H - 16)
	_wander(delta)
	_ride_boat(delta)
	_check_greetings()
	_check_eggs()
	_check_veil()

func _in_water(p: Vector2) -> bool:
	return p.y >= 1500.0

func _on_boardwalk(p: Vector2) -> bool:
	return p.x >= 680.0 and p.x <= 760.0 and p.y >= 1420.0

func _in_forest(p: Vector2) -> bool:
	return p.x >= 950.0 and p.y >= 250.0 and p.y <= 1250.0

func _wander(delta):
	wander_timer -= delta
	if wander_timer <= 0.0:
		wander_timer = randf_range(1.5, 3.5)
		ox_dir = Vector2(randf_range(-1, 1), randf_range(-1, 1)).normalized()
		bison_dir = Vector2(randf_range(-1, 1), randf_range(-1, 1)).normalized()
	ox.position += ox_dir * 30.0 * delta
	bison.position += bison_dir * 26.0 * delta
	ox.position.x = clamp(ox.position.x, 60, 900)
	ox.position.y = clamp(ox.position.y, 200, 1400)
	bison.position.x = clamp(bison.position.x, 60, 900)
	bison.position.y = clamp(bison.position.y, 200, 1400)

func _ride_boat(delta):
	boat.position.x += boat_dir * 60.0 * delta
	if boat.position.x > 1300.0:
		boat_dir = -1.0
	elif boat.position.x < 140.0:
		boat_dir = 1.0
	if player.position.distance_to(boat.position) < 70.0:
		player.position.x += boat_dir * 60.0 * delta

func _check_greetings():
	if not ox_greeted and player.position.distance_to(ox.position) < 70.0:
		ox_greeted = true
		_show_toast("The ox greets you first, as it should be.")
		_update_quest()
	elif not bison_greeted and player.position.distance_to(bison.position) < 70.0:
		if ox_greeted:
			bison_greeted = true
			_show_toast("The bison greets you next. The veil waits.")
			_update_quest()
		else:
			_show_toast("The bison waits — greet the ox first.")
			bison.position += Vector2(0, 40)

func _check_eggs():
	if not egg_feather_done and player.position.distance_to(Vector2(150, 200)) < 50.0:
		egg_feather_done = true
		eggs_found += 1
		_show_toast("Something small and bright found its way to you.")
		_update_quest()
	if not egg_clearing_done and player.position.distance_to(Vector2(1200, 700)) < 60.0:
		egg_clearing_done = true
		eggs_found += 1
		_show_toast("A quiet clearing, deep in the green.")
		_update_quest()
	if not egg_plank_done and player.position.distance_to(Vector2(720, 1900)) < 50.0:
		egg_plank_done = true
		eggs_found += 1
		_show_toast("The last plank, at the water's edge.")
		_update_quest()

func _check_veil():
	if vilon_done:
		return
	var p = player.position
	if p.x >= 620.0 and p.x <= 820.0 and p.y <= 60.0:
		if ox_greeted and bison_greeted:
			vilon_done = true
			var cfg = ConfigFile.new()
			cfg.load("user://heavens_progress.cfg")
			cfg.set_value("realms", "vilon_walked", true)
			cfg.save("user://heavens_progress.cfg")
			_show_toast("Vilon walked! The veil opens. Back to Realms to see it marked.")
			_update_quest()
		else:
			_show_toast("The veil waits — greet the Ox, then the Bison first.")
			player.position.y = 80.0
