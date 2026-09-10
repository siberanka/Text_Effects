void processSpinEffect(inout vec4 vertex, float speed, float axis, bool oneShot, float delay) {
    if (speed <= 0.0) speed = 2500.0;
    float time = GameTime * speed;

    float cosA;
    if (oneShot) {
        if (time > PI * 2.0) {
            cosA = 1.0;
        } else {
            cosA = cos(time);
        }
    } else {
        float period = PI * 2.0;
        float cycle = mod(time, period + delay);
        if (cycle < period) {
            cosA = cos(cycle);
        } else {
            cosA = 1.0;
        }
    }

    spinFlip = (cosA < 0.0) ? 1.0 : 0.0;
    spinScale = abs(cosA);

    spinT0 = vec3(0.0);
    spinT1 = vec3(0.0);
    spinT2 = vec3(0.0);
    spinT3 = vec3(0.0);
    captureTextEffectSpinCorners(texCoord0);

    gl_Position = ProjMat * ModelViewMat * vertex;
}

void processSpin(inout vec4 vertex, float speed, float axis) {
    processSpinEffect(vertex, speed, axis, false, 0.0);
}

void processOneSpin(inout vec4 vertex, float speed, float axis) {
    processSpinEffect(vertex, speed, axis, true, 0.0);
}

void processSequentialSpin(inout vec4 vertex, float speed, float axis) {
    if (speed <= 0.0) speed = 2500.0;

    float charIndex = (ProjMat[3][3] != 0.0)
        ? floor(Position.x / 6.0)
        : textEffectCharacterIndex();
    float t = mod((charIndex * 0.4 - GameTime * speed / TAU), 5.0);

    float cosA;
    if (t > 1.0) {
        cosA = 1.0;
    } else {
        cosA = cos(TAU * t);
    }

    spinFlip = (cosA < 0.0) ? 1.0 : 0.0;
    spinScale = abs(cosA);

    spinT0 = vec3(0.0);
    spinT1 = vec3(0.0);
    spinT2 = vec3(0.0);
    spinT3 = vec3(0.0);
    captureTextEffectSpinCorners(texCoord0);

    gl_Position = ProjMat * ModelViewMat * vertex;
}
