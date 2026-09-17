#!/usr/bin/env python3
"""Work out which TFLite output tensor is the confidence head and which is the
teaching head.

This used to be done by class count -- `if last_dim == 3: confidence`. That
worked only while the two heads had different widths. Once the teaching head was
shrunk from 6 classes to 3 both heads became [1, 3], the size test started
matching the same output twice, and everything downstream silently broke:
train.py wrote golden vectors whose expect_teaching actually held confidence
predictions, and the firmware left one head pointer null and refused to boot.

Order is not a safe fallback either -- the converter does not promise to emit
outputs in the order the Keras model declared them (here it reverses them).

What IS reliable is the signature. `tf.keras.Model(inp, [out_cs, out_ta])`
declares confidence first, so the converter names the signature outputs
`output_0` (confidence) and `output_1` (teaching), and the signature carries the
tensor index each name refers to. That survives reordering and equal widths.
"""
CONF_HINTS = ("conf", "cs")
TEACH_HINTS = ("teach", "ta")

# Keras declaration order in train.py: Model(inp, [out_cs, out_ta])
ORDINAL_ORDER = ("confidence", "teaching")


def _by_name(sig_outputs):
    """Map head -> tensor index using signature output names."""
    picked = {}
    for name, det in sig_outputs.items():
        low = name.lower()
        if any(h in low for h in CONF_HINTS):
            picked["confidence"] = int(det["index"])
        elif any(h in low for h in TEACH_HINTS):
            picked["teaching"] = int(det["index"])
    if len(picked) == 2:
        return picked

    # Unnamed heads: `output_<n>` is the Keras output ordinal.
    ordinals = {}
    for name, det in sig_outputs.items():
        stem = name.lower().rsplit("_", 1)[-1]
        if stem.isdigit():
            ordinals[int(stem)] = int(det["index"])
    if sorted(ordinals) == list(range(len(ORDINAL_ORDER))):
        return {ORDINAL_ORDER[i]: ordinals[i] for i in sorted(ordinals)}
    return None


def _by_size(out_details, n_conf, n_teach):
    """Last-resort fallback, valid only while the two heads differ in width."""
    if n_conf == n_teach:
        return None
    picked = {}
    for d in out_details:
        n = int(d["shape"][-1])
        if n == n_conf:
            picked["confidence"] = int(d["index"])
        elif n == n_teach:
            picked["teaching"] = int(d["index"])
    return picked if len(picked) == 2 else None


def resolve_heads(interp, n_conf, n_teach):
    """Return {'confidence': info, 'teaching': info}.

    Each info is a dict with:
      tensor_index -- the tflite tensor index (for interp.get_tensor)
      output_pos   -- position in get_output_details(), i.e. the C++
                      interpreter->output(i) argument
      scale, zero_point, classes
    """
    out_details = interp.get_output_details()
    by_index = {int(d["index"]): (i, d) for i, d in enumerate(out_details)}

    picked = None
    try:
        picked = _by_name(interp.get_signature_runner().get_output_details())
    except Exception:
        picked = None
    if picked is None:
        picked = _by_size(out_details, n_conf, n_teach)
    if picked is None:
        raise SystemExit(
            "cannot tell the two model outputs apart: the signature carries no "
            "usable names and both heads are the same width. Give the Keras "
            "outputs explicit names in train.py and retrain."
        )

    heads = {}
    expect = {"confidence": n_conf, "teaching": n_teach}
    for head, tensor_index in picked.items():
        if tensor_index not in by_index:
            raise SystemExit(f"{head} head points at tensor {tensor_index}, "
                             "which is not a model output")
        pos, det = by_index[tensor_index]
        n = int(det["shape"][-1])
        if n != expect[head]:
            raise SystemExit(f"{head} head has {n} classes, expected {expect[head]} "
                             "-- model and rule engine are out of sync, retrain")
        scale, zp = det["quantization"]
        heads[head] = {
            "tensor_index": tensor_index,
            "output_pos": pos,
            "scale": float(scale),
            "zero_point": int(zp),
            "classes": n,
        }
    if heads["confidence"]["tensor_index"] == heads["teaching"]["tensor_index"]:
        raise SystemExit("both heads resolved to the same output tensor")
    return heads
