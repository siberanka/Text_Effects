#ifndef TEXT_EFFECTS_26_3_SCALE_GLSL
#define TEXT_EFFECTS_26_3_SCALE_GLSL

void processScaleEffect(inout vec4 vertex, float expansion, float offsetX, float offsetY) {
    vec2 dir = textEffectCornerDirection();

    float actualExpansion = (expansion - 1.0) * 4.0;
    dir *= vec2(0.7, 1.0);
    vec2 finalOffset = dir * actualExpansion + vec2(offsetX, offsetY);

    setOffset(finalOffset.x, finalOffset.y);
    applyOffset(vertex);

    applyProjection(vertex);
    finalize();
}
#endif // TEXT_EFFECTS_26_3_SCALE_GLSL
