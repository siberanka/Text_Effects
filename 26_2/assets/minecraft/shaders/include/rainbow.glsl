// Author: nattapat2871 (https://nattapat2871.me)
void applyHueColor(float speed, float xPos, float yPos, float alpha) {
    if (speed <= 0.0) speed = 1000.0;

    vec4 texColor = get_lightmap_color();

    // Model-space keeps GUI text stable; screen-space keeps 26.2 staged world
    // draws independent of their arbitrary gl_VertexID base.
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
