// GENERATED companion to model_weights.h -- DO NOT EDIT
// Forward pass: Input(8) -> Dense(32,ReLU) -> Dense(16,ReLU) -> [Dense(3) TA, Dense(3) CS]
// Inference time: ~0.1ms at 240 MHz (917 multiply-adds, no library needed)
#pragma once
#include "model_weights.h"
#include "rule_engine.h"   // for Features struct and normalize_features()

// Dense layer: out[j] = bias[j] + sum_i(in[i] * W[i*out_n + j]), then ReLU
static inline void _ml_dense_relu(const float *W, const float *b,
                                   const float *in, int in_n,
                                   float *out, int out_n) {
    for (int j = 0; j < out_n; j++) {
        float s = b[j];
        for (int i = 0; i < in_n; i++) s += in[i] * W[i * out_n + j];
        out[j] = s > 0.0f ? s : 0.0f;
    }
}

// Dense layer without activation (output layer)
static inline void _ml_dense(const float *W, const float *b,
                               const float *in, int in_n,
                               float *out, int out_n) {
    for (int j = 0; j < out_n; j++) {
        float s = b[j];
        for (int i = 0; i < in_n; i++) s += in[i] * W[i * out_n + j];
        out[j] = s;
    }
}

static inline int _ml_argmax(const float *x, int n) {
    int m = 0;
    for (int i = 1; i < n; i++) if (x[i] > x[m]) m = i;
    return m;
}

// Run both heads in one call.
// f       : pointer to a filled Features struct (from rule_engine.h)
// out_ta  : 0=REPEAT, 1=HINT, 2=NORMAL_PRACTICE
// out_cs  : 0=CONFIDENT, 1=HESITANT, 2=GUESSING
static inline void ml_infer(const Features *f, int *out_ta, int *out_cs) {
    float norm[ML_FEATURE_COUNT];
    normalize_features(f, norm);

    float h0[ML_HIDDEN1], h1[ML_HIDDEN2], logits[ML_OUTPUT];

    // --- teaching action head ---
    _ml_dense_relu(ML_TA_W0, ML_TA_B0, norm, ML_FEATURE_COUNT, h0, ML_HIDDEN1);
    _ml_dense_relu(ML_TA_W1, ML_TA_B1, h0,   ML_HIDDEN1,       h1, ML_HIDDEN2);
    _ml_dense     (ML_TA_W2, ML_TA_B2, h1,   ML_HIDDEN2, logits, ML_OUTPUT);
    *out_ta = _ml_argmax(logits, ML_OUTPUT);

    // --- confidence state head ---
    _ml_dense_relu(ML_CS_W0, ML_CS_B0, norm, ML_FEATURE_COUNT, h0, ML_HIDDEN1);
    _ml_dense_relu(ML_CS_W1, ML_CS_B1, h0,   ML_HIDDEN1,       h1, ML_HIDDEN2);
    _ml_dense     (ML_CS_W2, ML_CS_B2, h1,   ML_HIDDEN2, logits, ML_OUTPUT);
    *out_cs = _ml_argmax(logits, ML_OUTPUT);
}
