"""Turn the images in assets/ into cut-outs and backgrounds.

Drop the Gemini images into assets/ with these names (PNG or JPG), then run `python3 prepare.py`.
Anything missing gets a drawn placeholder so the whole Short still renders.

  assets/chemist_k1.png   pose ك١ (raising the bottle, proud)
  assets/chemist_k2.png   pose ك٢ (hands on head, shocked)
  assets/worker.png       the 1880 worker rolling by hand
  assets/young.png        the young man on the floor with the phone
  assets/lab.png          old lab background (9:16)
  assets/factory.png      1880s factory background (9:16)
  assets/machine.png      the cigarette rolling machine (on white)
  assets/room.png         the navy room from the project file (optional)
  assets/logo.png         the official logo, transparent PNG (optional)
  assets/logo_eye.png     the «الباء بالعين» logo frame, transparent PNG (optional)
"""
import os, sys, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import basira_engine as E
import props as P

HERE = os.path.dirname(os.path.abspath(__file__))
E.setup(HERE, os.path.join(HERE, "font", "ReemKufi-Bold.ttf"))
A = os.path.join(HERE, "assets")


def find(name):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = os.path.join(A, name + ext)
        if os.path.exists(p): return p
    return None


def logo_cut(src, dst):
    """Logo on flat cream -> transparent PNG cropped to the artwork (the thin guide lines are dropped)."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(src).convert("RGB")).astype(float)
    bg = np.median(np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3)]), axis=0)
    d = np.abs(a - bg).max(axis=2)
    alpha = np.clip((d - 18) / 50, 0, 1)
    rows = (alpha > 0.5).sum(axis=1)
    alpha[rows > a.shape[1] * 0.6] = 0                      # full-width guide lines
    ys, xs = np.where(alpha > 0.5)
    y0, y1, x0, x1 = ys.min() - 10, ys.max() + 10, xs.min() - 10, xs.max() + 10
    rgba = np.dstack([a, alpha * 255]).astype(np.uint8)[y0:y1, x0:x1]
    Image.fromarray(rgba, "RGBA").save(dst)


def main():
    status = {}
    for name in ("chemist_k1", "chemist_k2", "worker", "young"):
        src = find(name)
        if not src:
            src = os.path.join(E.ROOT, "cut", "_ph_" + name + ".png"); P.placeholder_figure(name).save(src)
        E.cutout(name, src)
        if find(name): E.match_orange(name)
        status[name] = "real" if find(name) else "placeholder"
    src = find("machine")
    if src:
        E.cutout("machine", src, border=6); status["machine"] = "real"
    else:                                   # cut-paper machine drawn in code, flywheel animated separately
        P.machine_body().save(os.path.join(E.ROOT, "cut", "machine.png")); status["machine"] = "drawn"
    for name in ("lab", "factory", "room"):
        src = find(name); dst = os.path.join(E.ROOT, "bg", name + ".png")
        if src:
            from PIL import Image
            Image.open(src).convert("RGB").save(dst)
        else:
            P.make_placeholder_bg(name, dst)
        status[name] = "real" if src else "placeholder"
    for name in ("logo", "logo_eye"):
        src = find(name)
        if src: logo_cut(src, os.path.join(E.ROOT, "cut", name + ".png"))
        status[name] = "real" if src else "placeholder"
    # Gemini props (cut-paper objects on white)
    offs = {}
    for name in ("bottle", "bottle_cracked", "bottle_morphine", "medal", "scale", "clock", "cigarettes", "notifications"):
        src = find(name)
        if src:
            offs[name] = E.cutout(name, src, border=8); status[name] = "real"
        else:
            status[name] = "missing"
    status["offsets"] = offs
    json.dump(status, open(os.path.join(E.ROOT, "cut", "status.json"), "w"), indent=1)
    for k, v in status.items(): print(f"{k:16s} {v}")


if __name__ == "__main__":
    main()
