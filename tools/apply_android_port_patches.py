#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def replace(path, old, new, tag):
    p = ROOT / path
    s = p.read_text()
    if new in s:
        print(f"android patch already applied: {tag}")
        return
    if old not in s:
        raise SystemExit(f"android patch anchor missing ({tag}) in {path}")
    p.write_text(s.replace(old, new, 1))
    print(f"android patch applied: {tag}")

replace("recomp-ui/src/common/launcher_platform_sdl2.c",
"""    if (s <= 0.0f) s = 1.0f;
    forced = forced_display_scale();
""",
"""    if (s <= 0.0f) s = 1.0f;
#ifdef __ANDROID__
    /* Handheld compromise: readable on a 1080p RP5 without recreating the
     * oversized desktop-HiDPI layout. */
    s = 1.25f;
#endif
    forced = forced_display_scale();
""", "Android launcher DPI")

replace("recomp-ui/src/consoles/snes/snes_profile.h",
'''static const char* const kPanelsSettingsSnes[]  = { "video", "audio", "hotkeys", NULL };''',
'''#ifdef __ANDROID__
static const char* const kPanelsSettingsSnes[]  = { "video", "audio", NULL };
#else
static const char* const kPanelsSettingsSnes[]  = { "video", "audio", "hotkeys", NULL };
#endif''', "Hide Android hotkeys panel")

replace("snesrecomp/runner/src/desktop/launcher_video.h",
'    game->aspect_setting_label = "Display aspect";\n',
'''#ifdef __ANDROID__
    game->aspect_setting_label = "Pixel aspect";
#else
    game->aspect_setting_label = "Display aspect";
#endif
''', "Pixel aspect label")

replace("snesrecomp/runner/src/desktop/launcher_video.h",
'''    game->aspect_setting_help =
        "4:3 recreates a traditional TV. 8:7 uses square pixels. "
        "1:1 presents the native picture in a square. "
        "Also controls pixel proportions in adaptive widescreen.";
''',
'''#ifdef __ANDROID__
    game->aspect_setting_help =
        "4:3 recreates a CRT. 8:7 uses square pixels. "
        "This is independent of true widescreen.";
#else
    game->aspect_setting_help =
        "4:3 recreates a traditional TV. 8:7 uses square pixels. "
        "1:1 presents the native picture in a square. "
        "Also controls pixel proportions in adaptive widescreen.";
#endif
''', "Pixel aspect help")

replace("recomp-ui/src/common/backends/imgui/launcher_imgui.cpp",
'''        row_window_scale(m, th);
        // Universal fullscreen row (every console; Off/Borderless/Exclusive,
        // the legacy launcher's vocabulary). Sits right under Window scale,
        // matching the old Display panel order.
        row_fullscreen(m, th);
''',
'''#ifndef __ANDROID__
        row_window_scale(m, th);
        row_fullscreen(m, th);
#endif
''', "Hide Android desktop window rows")

replace("recomp-ui/src/common/backends/imgui/launcher_imgui.cpp",
'''    // Universal fullscreen row (every console — no longer gated on the
    // vestigial has_fullscreen_toggle). A tri-state dropdown, so Exclusive is
    // both reachable and visible without pressing through the other two.
    row_fullscreen(m, th);
''',
'''#ifndef __ANDROID__
    row_fullscreen(m, th);
#endif
''', "Hide Android deep fullscreen row")

p = ROOT / "recomp-ui/src/common/backends/imgui/launcher_imgui.cpp"
s = p.read_text()
marker = "// True when this game exposes ANY of the deeper PSX-style DISPLAY controls.\n"
helper = r'''#ifdef __ANDROID__
static bool android_mmx_widescreen_feature(LauncherModel* m,
                                           RecompLauncherCModFeature* out) {
    const auto* mods = m ? m->mods : nullptr;
    if (!mods || !mods->feature_count || !mods->feature_get) return false;
    for (int i = 0; i < mods->feature_count(mods->ctx); ++i) {
        RecompLauncherCModFeature f{};
        if (!mods->feature_get(mods->ctx, i, &f)) continue;
        if (!std::strcmp(f.package_id, "megaman-x.enhancement.widescreen") &&
            !std::strcmp(f.id, "widescreen")) {
            if (out) *out = f;
            return true;
        }
    }
    return false;
}

static void draw_android_mmx_widescreen_row(LauncherModel* m,
                                             const LauncherTheme& th) {
    RecompLauncherCModFeature feature{};
    if (!android_mmx_widescreen_feature(m, &feature)) return;
    const auto* mods = m->mods;
    if (!mods->feature_option_get || !mods->feature_choice_get ||
        !mods->feature_enable || !mods->feature_set_option) return;
    RecompLauncherCModOption aspect{};
    bool found = false;
    for (int i = 0; i < feature.option_count; ++i) {
        RecompLauncherCModOption opt{};
        if (mods->feature_option_get(mods->ctx, feature.package_id,
                                     feature.id, i, &opt) &&
            !std::strcmp(opt.id, "aspect")) {
            aspect = opt; found = true; break;
        }
    }
    if (!found) return;
    char preview[128] = "Off";
    if (feature.enabled) {
        std::snprintf(preview, sizeof(preview), "%s",
                      aspect.value[0] ? aspect.value : "Adaptive");
        for (int i = 0; i < aspect.choice_count; ++i) {
            RecompLauncherCModChoice choice{};
            if (mods->feature_choice_get(mods->ctx, feature.package_id,
                                         feature.id, aspect.id, i, &choice) &&
                !std::strcmp(choice.value, aspect.value)) {
                std::snprintf(preview, sizeof(preview), "%s", choice.label);
                break;
            }
        }
    }
    row_label_right("Widescreen", th, px(180));
    ImGui::SetNextItemWidth(px(180));
    if (ImGui::BeginCombo("##mmx_widescreen", ui_text(preview))) {
        if (ImGui::Selectable(ui_text("Off"), !feature.enabled))
            mods->feature_enable(mods->ctx, feature.package_id, feature.id, 0);
        for (int i = 0; i < aspect.choice_count; ++i) {
            RecompLauncherCModChoice choice{};
            if (!mods->feature_choice_get(mods->ctx, feature.package_id,
                                          feature.id, aspect.id, i, &choice))
                continue;
            bool selected = feature.enabled &&
                            !std::strcmp(choice.value, aspect.value);
            if (ImGui::Selectable(ui_text(choice.label), selected)) {
                if (!feature.enabled)
                    mods->feature_enable(mods->ctx, feature.package_id,
                                         feature.id, 1);
                mods->feature_set_option(mods->ctx, feature.package_id,
                                         feature.id, aspect.id, choice.value);
            }
        }
        ImGui::EndCombo();
    }
    if (ImGui::IsItemHovered(ImGuiHoveredFlags_DelayNormal))
        ImGui::SetTooltip("Expand the actual stage view. 16:9 is recommended on the RP5.");
}
#endif

'''
if helper not in s:
    if marker not in s: raise SystemExit("widescreen helper anchor missing")
    s = s.replace(marker, helper + marker, 1)
legacy = "        draw_aspect_row(m, th);\n"
legacy_new = "        draw_aspect_row(m, th);\n#ifdef __ANDROID__\n        draw_android_mmx_widescreen_row(m, th);\n#endif\n"
if legacy_new not in s:
    if legacy not in s: raise SystemExit("legacy widescreen row anchor missing")
    s = s.replace(legacy, legacy_new, 1)
deep = "    draw_aspect_row(m, th);\n\n    if (m->has_sharp_filter) {\n"
deep_new = "    draw_aspect_row(m, th);\n#ifdef __ANDROID__\n    draw_android_mmx_widescreen_row(m, th);\n#endif\n\n    if (m->has_sharp_filter) {\n"
if deep_new not in s:
    if deep not in s: raise SystemExit("deep widescreen row anchor missing")
    s = s.replace(deep, deep_new, 1)
p.write_text(s)

p = ROOT / "snesrecomp/runner/src/desktop/host_main.c"
s = p.read_text()
proto = "static void HandleGamepadInput(GamepadInfo *gi, int button, bool pressed);\n"
proto_new = proto + "#ifdef __ANDROID__\nstatic void AndroidPollGamepads(void);\n#endif\n"
if proto_new not in s:
    if proto not in s: raise SystemExit("gamepad prototype anchor missing")
    s = s.replace(proto, proto_new, 1)
anchor = "\n/* ── config.ini discovery ─────────────────────────────────────────────────── */\n"
poll = r'''
#ifdef __ANDROID__
static void AndroidPollGamepads(void) {
  static const uint8 raw_buttons[] = {
    kGamepadBtn_A, kGamepadBtn_B, kGamepadBtn_X, kGamepadBtn_Y,
    kGamepadBtn_Back, kGamepadBtn_Guide, kGamepadBtn_Start,
    kGamepadBtn_L3, kGamepadBtn_R3, kGamepadBtn_L1, kGamepadBtn_R1,
    kGamepadBtn_DpadUp, kGamepadBtn_DpadDown,
    kGamepadBtn_DpadLeft, kGamepadBtn_DpadRight
  };
  SDL_GameControllerUpdate();
  SDL_JoystickUpdate();
  for (int slot = 0; slot < 2; ++slot) {
    GamepadInfo *gi = &g_gamepad[slot];
    if (gi->joystick_id == -1) continue;
    if (!gi->raw_joystick) {
      SDL_GameController *gc = SDL_GameControllerFromInstanceID(gi->joystick_id);
      if (!gc) continue;
      for (int b = 0; b < SDL_CONTROLLER_BUTTON_MAX; ++b) {
        int mapped = RemapSdlButton(b);
        if (mapped >= 0)
          HandleGamepadInput(gi, mapped,
              SDL_GameControllerGetButton(gc, (SDL_GameControllerButton)b) != 0);
      }
      HandleGamepadAxisInput(gi, SDL_CONTROLLER_AXIS_LEFTX,
          SDL_GameControllerGetAxis(gc, SDL_CONTROLLER_AXIS_LEFTX));
      HandleGamepadAxisInput(gi, SDL_CONTROLLER_AXIS_LEFTY,
          SDL_GameControllerGetAxis(gc, SDL_CONTROLLER_AXIS_LEFTY));
    } else if (gi->joystick) {
      int nb = SDL_JoystickNumButtons(gi->joystick);
      if (nb > (int)(sizeof(raw_buttons) / sizeof(raw_buttons[0])))
        nb = (int)(sizeof(raw_buttons) / sizeof(raw_buttons[0]));
      for (int b = 0; b < nb; ++b)
        HandleGamepadInput(gi, raw_buttons[b],
                           SDL_JoystickGetButton(gi->joystick, b) != 0);
      if (SDL_JoystickNumAxes(gi->joystick) >= 2) {
        HandleGamepadAxisInput(gi, SDL_CONTROLLER_AXIS_LEFTX,
                               SDL_JoystickGetAxis(gi->joystick, 0));
        HandleGamepadAxisInput(gi, SDL_CONTROLLER_AXIS_LEFTY,
                               SDL_JoystickGetAxis(gi->joystick, 1));
      }
      if (SDL_JoystickNumHats(gi->joystick) > 0) {
        Uint8 hat = SDL_JoystickGetHat(gi->joystick, 0);
        HandleGamepadInput(gi, kGamepadBtn_DpadUp, (hat & SDL_HAT_UP) != 0);
        HandleGamepadInput(gi, kGamepadBtn_DpadDown, (hat & SDL_HAT_DOWN) != 0);
        HandleGamepadInput(gi, kGamepadBtn_DpadLeft, (hat & SDL_HAT_LEFT) != 0);
        HandleGamepadInput(gi, kGamepadBtn_DpadRight, (hat & SDL_HAT_RIGHT) != 0);
      }
    }
  }
}
#endif
'''
if "static void AndroidPollGamepads(void) {" not in s:
    if anchor not in s: raise SystemExit("gamepad poll anchor missing")
    s = s.replace(anchor, "\n" + poll + anchor, 1)
loop = "    if (!running)\n      break;\n    OverlaySelftestPadMainTick(frameCtr);\n"
loop_new = "    if (!running)\n      break;\n#ifdef __ANDROID__\n    AndroidPollGamepads();\n#endif\n    OverlaySelftestPadMainTick(frameCtr);\n"
if loop_new not in s:
    if loop not in s: raise SystemExit("gamepad loop anchor missing")
    s = s.replace(loop, loop_new, 1)

p = ROOT / "snesrecomp/runner/src/desktop/host_main.c"
s = p.read_text()
seed_old = """  ls->linear_filter = g_config.linear_filtering;
  ls->aspect_index = SnesDisplayAspect_Clamp(g_config.display_aspect);
"""
seed_new = """  ls->linear_filter = g_config.linear_filtering;
  ls->widescreen    = g_config.widescreen ? 1 : 0;
  ls->aspect_index = SnesDisplayAspect_Clamp(g_config.display_aspect);
"""
if seed_new not in s:
    if seed_old not in s: raise SystemExit("widescreen seed anchor missing")
    s = s.replace(seed_old, seed_new, 1)
commit_old = """  g_config.linear_filtering    = ls->linear_filter != 0;
  if (game->display_aspect_supported)
"""
commit_new = """  g_config.linear_filtering    = ls->linear_filter != 0;
  if (game->widescreen_supported)
    g_config.widescreen = ls->widescreen != 0;
  if (game->display_aspect_supported)
"""
if commit_new not in s:
    if commit_old not in s: raise SystemExit("widescreen commit anchor missing")
    s = s.replace(commit_old, commit_new, 1)
p.write_text(s)

p.write_text(s)
print("Android/RP5 framework patches ready")
