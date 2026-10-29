extends Control
# Pandora Heavens Realms — Godot 4, V1.03, 2026-10-28.
# V1.03 adds the first PLAYABLE realm: Vilon (vilon.tscn / vilon.gd).
# The V1.02 hub fix stands: no hub gate, START goes straight to Vilon,
# every realm has its own big button, PLAY VILON walks the realm itself.
# Curtis names the lands, Wren and Rebecka lay the lands and cattle.
# No real fingerprint data is collected or stored here.

var realms = [
	{"name": "1. Vilon (or Araphel)", "desc": "Closest to Earth; a curtain or veil; atmospheric phenomena; sometimes the abode of Adam and Eve; ruled by Gabriel. Safari animals and realism, plus rainforest too, dedicated to the 1st layer."},
	{"name": "2. Raqia", "desc": "The firmament where stars/planets are fixed; place of fallen angels in some accounts; ruled by Raphael (sometimes with Zachariel). Rendering and mapping: No Man's Sky infrastructure."},
	{"name": "3. Shehaqim", "desc": "Skies/clouds; produces manna; contains Paradise (Garden of Eden) and sometimes Hell on the northern side; third heaven Paul refers to in 2 Corinthians 12. Tied to the cat of nine heads and nine tails."},
	{"name": "4. Maon", "desc": "Heavenly Jerusalem, Temple, and Altar; ruled by Michael. Astral Temple of Heaven, not tied to chaos."},
	{"name": "5. Makhon — HOME", "desc": "Fixed place; angels (Ishim) and choirs; trials and visitations. Basically Valhalla's walking grounds. Curtis guards the gates and carries the wrath of fear so his cat stays within a whistling distance. Thats home then. Access: mystics and deities, with a proper purchased code."},
	{"name": "6. Zebul", "desc": "Lofty abode; domain of certain angelic groups and records. Mass knowledge library."},
	{"name": "7. Araboth — STRICTLY VIP", "desc": "Highest heaven; Throne of God, Seraphim, Cherubim, and unborn souls; ruled by Cassiel. Strictly VIP: Curtis's or John's fingerprints, and the users PI fingerprints scanner. Starter keys for parents: Google thumb drive with fingerprint scanner, because Curtis and John will not always be available."},
]

var realm_index = 0
var started = false

func _ready():
	$Scroll/Box/StartButton.pressed.connect(_on_start_pressed)
	$Scroll/Box/PlayButton.pressed.connect(_on_play_pressed)
	$Scroll/Box/NextButton.pressed.connect(_on_next_pressed)
	# One big button per realm — no hub, no gate, tap any realm directly.
	for i in realms.size():
		var b = Button.new()
		b.text = realms[i]["name"] + " — Enter"
		b.custom_minimum_size = Vector2(0, 80)
		b.pressed.connect(_on_realm_button_pressed.bind(i))
		$Scroll/Box/RealmButtons.add_child(b)
	_show_realm()

func _show_realm():
	var r = realms[realm_index]
	var cfg = ConfigFile.new()
	var walked = ""
	if cfg.load("user://heavens_progress.cfg") == OK and cfg.get_value("realms", "vilon_walked", false):
		walked = " — Vilon WALKED"
		$Scroll/Box/Title.text = "Pandora Heavens Realms — V1.03 — Vilon WALKED"
	var prefix = "V1.03" + walked + " — " + ("STARTED" if started else "READY — tap START, PLAY VILON, or any realm below") + "\n\n"
	$Scroll/Box/RealmLabel.text = prefix + r["name"] + "\n\n" + r["desc"] + "\n\nCattle, first and foremost: Ox first, bison next.\nWetlands: low water lands, marsh, swamp, reeds, boats, bridges, boardwalks.\nMobile: Google, Meta Quest, VR, AR glasses, aura ring.\nPotential partners: IMAX, Ubisoft, Anthropix, Unreal Engine.\nGoal: First with AR open world gaming."

func _on_start_pressed():
	started = true
	realm_index = 0
	_show_realm()

func _on_play_pressed():
	get_tree().change_scene_to_file("res://vilon.tscn")

func _on_next_pressed():
	started = true
	realm_index = (realm_index + 1) % realms.size()
	_show_realm()

func _on_realm_button_pressed(i):
	started = true
	realm_index = i
	_show_realm()
