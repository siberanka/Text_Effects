#ifndef TEXT_EFFECTS_26_2_TEXT_EFFECTS_UTILS_GLSL
#define TEXT_EFFECTS_26_2_TEXT_EFFECTS_UTILS_GLSL

#moj_import <minecraft:common.glsl>
#moj_import <minecraft:offset.glsl>
#moj_import <minecraft:defaults.glsl>
#moj_import <minecraft:rainbow.glsl>
#moj_import <minecraft:spin.glsl>
#moj_import <minecraft:text_effects_api.glsl>
#moj_import <minecraft:apply_effect.glsl>

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
    // override); the text display's own opacity (Color.a) is applied
    // separately at the very end of the pipeline.
    currentVertex = vertex;
    currentBaseColor = vec4(Color.rgb, 1.0);
    currentIsShadow = false;
    currentApplyToShadow = false;

    // ============================================
    // Config-based color-effect mappings
    // ============================================
    #moj_import <minecraft:_config.glsl>

    // Every configured upstream or custom effect enters this path.
    if (hasAnyEffect()) {
        applyEffect(currentVertex, currentBaseColor, currentIsShadow);
        return;
    }

    // Plain vanilla colors, Unicode glyphs, and bitmap/color glyphs all enter
    // this path. Use the same 26.2 reversed-depth bias as configured effects.
    applyProjection(vertex);
    applyTextDisplayDepthBias();
    applyColorTexture();
    finalize();
}

#endif // TEXT_EFFECTS_26_2_TEXT_EFFECTS_UTILS_GLSL
