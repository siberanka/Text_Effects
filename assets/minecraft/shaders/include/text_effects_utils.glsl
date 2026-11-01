#moj_import <common.glsl>
#moj_import <offset.glsl>
#moj_import <defaults.glsl>
#moj_import <rainbow.glsl>
#moj_import <wavy.glsl>
#moj_import <bouncy.glsl>
#moj_import <blinking.glsl>
#moj_import <pulse.glsl>
#moj_import <spin.glsl>
#moj_import <shake.glsl>
#moj_import <fade.glsl>
#moj_import <iterating.glsl>
#moj_import <glitch.glsl>
#moj_import <gradient.glsl>
#moj_import <scale.glsl>
#moj_import <text_effects_api.glsl>
#moj_import <apply_effect.glsl>

// ============================================================
// TEXT EFFECTS - Config-based System
// ============================================================
// Edit _config.glsl to customize color-effect mappings
// ============================================================

// Compare the trigger color (0-255) against a color from rgb()/rgba()/argb().
// vec4 inputs (rgba/argb) ignore alpha.
bool colorMatches(ivec3 c, vec3 target) {
    return c == ivec3(target * 255.0 + 0.5);
}
bool colorMatches(ivec3 c, vec4 target) {
    return colorMatches(c, target.rgb);
}

// Match the main color OR its shadow (~25% of main); flags shadow on a shadow match.
bool checkAndSetShadow(ivec3 c, vec3 target) {
    ivec3 t = ivec3(target * 255.0 + 0.5);
    if (c == t) {
        return true;
    }
    if (c == t / 4) {
        currentIsShadow = true;
        return currentIsShadow;
    }
    return false;
}
bool checkAndSetShadow(ivec3 c, vec4 target) {
    return checkAndSetShadow(c, target.rgb);
}

// TEXT_EFFECT macro: matches a color (exact). Pass rgb()/rgba()/argb(); alpha ignored.
#define TEXT_EFFECT(COLOR) if (colorMatches(c, COLOR))

// TEXT_EFFECT_WITH_SHADOW macro: matches a color AND its shadow (exact).
#define TEXT_EFFECT_WITH_SHADOW(COLOR) if (checkAndSetShadow(c, COLOR))

void applyTextEffects() {
    vec4 vertex = vec4(Position, 1.0);
    ivec3 c = ivec3(Color.rgb * 255.0 + 0.5);

    // Initialize global state. currentBaseColor.a defaults to 1.0 (no user
    // override) — the text display's own opacity (Color.a) is applied
    // separately at the very end of the pipeline.
    currentVertex = vertex;
    currentBaseColor = vec4(Color.rgb, 1.0);
    currentIsShadow = false;
    currentApplyToShadow = false;

    // ============================================
    // Config-based color-effect mappings
    // ============================================
    #moj_import <_config.glsl>

    // If any effect was applied, execute it
    if (hasAnyEffect()) {
        applyEffect(currentVertex, currentBaseColor, currentIsShadow);
        return;
    }

    // === No effect matched, render normally ===
    applyProjection(vertex);
    // Match the effect path's depth bias so effect-triggered shadows don't
    // z-fight with normally-rendered main text. Skip in GUI (ortho) because
    // 1.21.6+ uses tight z-steps for UI layering — a 0.001 nudge there flips
    // tooltip/autocomplete ordering relative to chat.
    if (ProjMat[3][3] == 0.0) {
        gl_Position.z -= gl_Position.w * 0.001;
    }
    applyColorTexture();
    finalize();
}
