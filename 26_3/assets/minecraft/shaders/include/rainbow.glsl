#ifndef TEXT_EFFECTS_26_3_RAINBOW_GLSL
#define TEXT_EFFECTS_26_3_RAINBOW_GLSL

// Author: nattapat2871 (https://nattapat2871.me)
void applyHueColor(float speed, float xPos, float yPos, float alpha) {
    if (speed <= 0.0) speed = 1000.0;

    vec4 texColor = get_lightmap_color();

    // Model-space in GUI and projected screen-space in world rendering keep
    // the phase stable when staged draw bases change.
    bool isGUI = ProjMat[3][3] != 0.0;
    float spatial;
    if (isGUI) {
        spatial = xPos + yPos;
    } else {
        vec2 screenPosition = textEffectScreenPosition();
        spatial = screenPosition.x + screenPosition.y;
    }

    vec3 rainbowColor = hue((GameTime * speed) + spatial * 0.01);
    vertexColor = vec4(rainbowColor, alpha) * texColor;
}

void applyHueColor(float speed, float xPos, float yPos) {
    applyHueColor(speed, xPos, yPos, 1.0);
}

void processRainbowEffect(inout vec4 vertex, float speed) {
    float xPos = vertex.x;
    float yPos = vertex.y;
    applyProjection(vertex);
    applyHueColor(speed, xPos, yPos);
    finalize();
}

#endif // TEXT_EFFECTS_26_3_RAINBOW_GLSL
