#ifndef TEXT_EFFECTS_26_3_BOUNCY_GLSL
#define TEXT_EFFECTS_26_3_BOUNCY_GLSL

void processBouncyEffect(inout vec4 vertex, float speed, float amp) {
    applyColorTexture();
    vec2 glyphCorner = textEffectGlyphCorner();

    if (speed <= 0.0) speed = 3000.0;
    if (amp <= 0.0) amp = 1.0;

    float time = GameTime * speed;

    if (glyphCorner.y < 0.5) {
        vertex.y += cos(time) * amp;
        vertex.y += max(cos(time) * amp, 0.);
    }
    applyProjection(vertex);
    finalize();
}

#endif // TEXT_EFFECTS_26_3_BOUNCY_GLSL
