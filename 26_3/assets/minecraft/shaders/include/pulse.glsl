#ifndef TEXT_EFFECTS_26_3_PULSE_GLSL
#define TEXT_EFFECTS_26_3_PULSE_GLSL

void processPulse(inout vec4 vertex, float speed, float size) {
    float time = GameTime * speed * 1000.0;
    float factor = (sin(time) * 0.5 + 0.5);

    float expansion = size * 2.5 * factor;

    vec2 dir = textEffectCornerDirection();

    dir *= vec2(0.7, 1.0);

    vec2 finalOffset = dir * expansion;
    setOffset(finalOffset.x, finalOffset.y);
    applyOffset(vertex);

    applyProjection(vertex);
    finalize();
}
#endif // TEXT_EFFECTS_26_3_PULSE_GLSL
