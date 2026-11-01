#ifndef TEXT_EFFECTS_26_2_COMMON_GLSL
#define TEXT_EFFECTS_26_2_COMMON_GLSL

// Author: nattapat2871 (https://nattapat2871.me)
#define PI 3.14159265359
#define TAU 6.28318530718

float random(vec2 seed) {
    return fract(sin(dot(seed, vec2(12.9898, 78.233))) * 43758.5453);
}

float noise(float n) {
    float i = floor(n);
    float f = fract(n);
    return mix(random(vec2(i, 0.0)), random(vec2(i + 1.0, 0.0)), smoothstep(0.0, 1.0, f));
}

vec3 hue(float t) {
    t = fract(t);
    float r = abs(t * 6.0 - 3.0) - 1.0;
    float g = 2.0 - abs(t * 6.0 - 2.0);
    float b = 2.0 - abs(t * 6.0 - 4.0);
    return clamp(vec3(r, g, b), 0.0, 1.0);
}

vec4 get_lightmap_color() {
#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
    return sample_lightmap(Sampler2, UV2);
#else
    return vec4(1.0);
#endif
}

void finalize() {
    // ColorModulator is applied once, in the fragment shader.

}

void applyProjection(inout vec4 vertex) {
    gl_Position = ProjMat * ModelViewMat * vertex;
}

// 26.2 appends text draws to a shared staged buffer, so gl_VertexID can start
// at any offset. Mojang's glyph quads retain a 0.01-texel atlas inset; at the
// fixed 256x256 glyph-sheet size its fractional texel identifies every corner
// for both grayscale Unicode and bitmap/color glyphs.
vec2 textEffectGlyphCorner() {
    return step(vec2(0.5), fract(UV0 * 256.0));
}

vec2 textEffectCornerDirection() {
    return textEffectGlyphCorner() * 2.0 - 1.0;
}

int textEffectLocalVertexIndex() {
    vec2 corner = textEffectGlyphCorner();
    if (corner.x < 0.5 && corner.y < 0.5) return 0;
    if (corner.x < 0.5 && corner.y > 0.5) return 1;
    if (corner.x > 0.5 && corner.y > 0.5) return 2;
    return 3;
}

float textEffectCharacterIndex() {
    // Removing the UV-derived local corner first prevents an unaligned staged
    // draw base from assigning two character IDs to one quad.
    return floor(float(gl_VertexID - textEffectLocalVertexIndex()) / 4.0);
}

vec2 textEffectScreenPosition() {
    float safeW = abs(gl_Position.w) < 0.000001
        ? (gl_Position.w < 0.0 ? -0.000001 : 0.000001)
        : gl_Position.w;
    return (gl_Position.xy / safeW) * ScreenSize * 0.5;
}

void captureTextEffectSpinCorners(vec2 uv) {
    vec2 corner = textEffectGlyphCorner();
    if (corner.x < 0.5 && corner.y < 0.5) spinT0 = vec3(uv, 1.0);
    if (corner.x < 0.5 && corner.y > 0.5) spinT2 = vec3(uv, 1.0);
    if (corner.x > 0.5 && corner.y > 0.5) spinT1 = vec3(uv, 1.0);
    if (corner.x > 0.5 && corner.y < 0.5) spinT3 = vec3(uv, 1.0);
}

void captureTextEffectFragmentCorners(vec2 uv) {
    vec2 corner = textEffectGlyphCorner();
    if (corner.x < 0.5 && corner.y < 0.5) fshGlyphT0 = vec3(uv, 1.0);
    if (corner.x < 0.5 && corner.y > 0.5) fshGlyphT2 = vec3(uv, 1.0);
    if (corner.x > 0.5 && corner.y > 0.5) fshGlyphT1 = vec3(uv, 1.0);
    if (corner.x > 0.5 && corner.y < 0.5) fshGlyphT3 = vec3(uv, 1.0);
}

// Minecraft 26.2 uses reversed depth for world text. Text displays render
// their glyphs against a coplanar background, so move every non-see-through
// glyph towards the camera by a constant 0.001 in normalized device depth.
// Scaling by clip-space W keeps the bias distance-independent.
void applyTextDisplayDepthBias() {
#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
    gl_Position.z += gl_Position.w * 0.001;
#endif
}

void applyColorTexture() {
    vertexColor = Color * get_lightmap_color();
}

#endif // TEXT_EFFECTS_26_2_COMMON_GLSL
