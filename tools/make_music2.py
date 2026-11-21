import numpy as np, sys, wave
try:
    from scipy.signal import lfilter
except Exception:
    lfilter = None
# usage: make_music2.py out.wav seconds style(house|trap|pop) seed
out, secs, style, seed = sys.argv[1], float(sys.argv[2]), sys.argv[3], int(sys.argv[4])
SR = 44100; rng = np.random.default_rng(seed)
n = int(secs * SR); L_ = np.zeros(n); R_ = np.zeros(n)
bpm = {"house": 126, "trap": 140, "pop": 118, "phonk": 130, "ibiza": 122}[style]
beat = 60 / bpm; bar = 4 * beat
prog = {"house": [(57,'m'),(53,''),(48,''),(55,'')],
        "trap":  [(57,'m'),(57,'m'),(53,''),(52,'')],
        "pop":   [(53,''),(55,''),(57,'m'),(52,'m')],
        "phonk": [(52,'m'),(52,'m'),(48,''),(50,'')],
        "ibiza": [(57,'m'),(55,''),(53,''),(52,'m')]}[style]
def f(m): return 440 * 2 ** ((m - 69) / 12)
def chord(r, q): return [r, r + (3 if q == 'm' else 4), r + 7]
def lp(x, a):
    if lfilter is not None: return lfilter([a], [1, a - 1], x)
    k = max(1, int(1 / a)); return np.convolve(x, np.ones(k) / k, 'same')
def saw(fr, t): return 2 * ((fr * t) % 1) - 1
def supersaw(m, L):
    t = np.arange(L) / SR
    return sum(saw(f(m) * (1 + d), t + rng.random()) for d in (-.012, -.006, 0, .006, .012)) / 5
def add(sig, t, pan=0., g=1.):
    i = int(t * SR)
    if i >= n or i < 0: return
    s = sig[:n - i] * g
    L_[i:i+len(s)] += s * (1 - pan); R_[i:i+len(s)] += s * (1 + pan)
def kick(L=.35, hi=160, lo=48, dec=8):
    t = np.arange(int(L * SR)) / SR
    return np.sin(2*np.pi*np.cumsum(lo + (hi-lo)*np.exp(-t*35))/SR) * np.exp(-t*dec)
def noise(L, dec): t = np.arange(int(L*SR))/SR; return rng.standard_normal(len(t)) * np.exp(-t*dec)
def hat(L=.04, dec=90): x = noise(L, dec); return np.diff(np.r_[0, x])
def clap():
    T = int(.2 * SR)
    x = sum(np.pad(np.r_[np.zeros(int(d*SR)), noise(.18, 25)], (0, T))[:T] for d in (0, .01, .02))
    return lp(x, .5) - lp(x, .05)
# sidechain envelope (pumping)
sc = np.ones(n)
if style != "trap":
    tt = np.arange(n) / SR; ph = (tt % beat) / beat
    sc = np.clip(.15 + ph * 3.5, 0, 1)
intro = bar  # first bar = build-up
# riser in intro
Lr = int(intro * SR); tr = np.arange(Lr) / SR
rn = rng.standard_normal(Lr)
riser = np.concatenate([lp(c, .02 + .4 * (i / 31) ** 2) for i, c in enumerate(np.array_split(rn, 32))]) * (tr / intro) ** 2
add(riser * .5, 0)
# snare roll in intro
steps = [0, 2, 4, 6, 8, 10, 11, 12, 13, 14, 14.5, 15, 15.5]
for s in steps: add(clap() * (.15 + .35 * s / 16), s * beat / 4)
k = 0; t0 = 0.0
while t0 < secs:
    r, q = prog[k % 4]; notes = chord(r, q); Lb = int(bar * SR); tb = np.arange(Lb) / SR
    drop = t0 >= intro - 1e-6
    # chords
    pad = sum(supersaw(m + 12, Lb) for m in notes) / 3
    pad = lp(pad, .25 if drop else .06)
    i0 = int(t0 * SR); seg = sc[i0:i0 + Lb]; seg = np.r_[seg, np.ones(Lb - len(seg))]
    add(pad * seg * (.28 if drop else .18), t0, -.2); add(pad * seg * (.28 if drop else .18), t0, .2)
    if drop:
        if style == "ibiza":
            def vox(m, L):  # "eee" vowel-like synth via formant-weighted harmonics
                t = np.arange(L)/SR; f0 = f(m); out = np.zeros(L)
                vib = 1 + .006*np.sin(2*np.pi*5.5*t)
                for h in range(1, 40):
                    fh = f0*h
                    if fh > 9000: break
                    w = sum(a*np.exp(-((fh-F)/bw)**2) for F, bw, a in ((300, 90, 1), (2300, 200, .5), (3000, 250, .35)))
                    out += w*np.sin(2*np.pi*np.cumsum(np.full(L, fh)*vib)/SR)/h**.3
                return out*env(L, .04, .15)
            def env(L, a, r):
                e = np.ones(L); A = min(int(a*SR), L); Rr = min(int(r*SR), L)
                e[:A] = np.linspace(0, 1, A); e[L-Rr:] *= np.linspace(1, 0, Rr); return e
            for j in range(4):
                add(kick(dec=9) * .9, t0 + j*beat)
                if j % 2: add(clap() * .35, t0 + j*beat)
                add(hat(.1, 35) * .16, t0 + (j+.5)*beat, .3)
                for s16 in range(4): add(hat(.03, 120) * (.07 if s16 % 2 else .04), t0 + (j+s16/4)*beat, -.4)
            for c, p in ((.75, 300), (1.5, 220), (2.75, 300), (3.25, 220), (3.5, 330)):
                Lc = int(.18*SR); tc = np.arange(Lc)/SR
                add(np.sin(2*np.pi*p*tc*(1+.3*np.exp(-tc*40)))*np.exp(-tc*22)*.22, t0 + c*beat, .45)
            for c in (0, 1.5, 2.5, 3.5):  # piano stabs
                Lp = int(.6*SR); tp = np.arange(Lp)/SR
                pn = sum(sum(np.sin(2*np.pi*f(m+12)*h*tp)*np.exp(-tp*(3+h*2))/h for h in (1,2,3,4)) for m in notes)
                add(pn*.09, t0 + c*beat, -.15)
            Lo = int(beat*SR)
            for j in range(4):
                to = np.arange(Lo)/SR; bm = r-12 if j < 3 else notes[2]-12
                add(np.tanh(1.5*np.sin(2*np.pi*f(bm)*to))*np.exp(-to*3)*.4, t0 + (j+.25)*beat)
            if k % 2 == 1:  # vocal hook every other bar
                hook = [(notes[2]+12, 0, 1.5), (notes[1]+12, 1.5, .5), (notes[2]+12, 2, 1.0), (notes[0]+12, 3, .9)]
            else:
                hook = [(notes[0]+12, 0, 1.0), (notes[2]+12, 2, 1.8)]
            for m, st, du in hook: add(vox(m, int(du*beat*SR))*.11, t0 + st*beat, .05)
        elif style == "house":
            for j in range(4):
                add(kick() * .9, t0 + j*beat)
                if j % 2: add(clap() * .45, t0 + j*beat)
                add(hat(.12, 30) * .18, t0 + (j + .5)*beat, .3)
                Lo = int(beat/2*SR); to = np.arange(Lo)/SR
                bs = lp(saw(f(r-12), to), .15) * np.exp(-to*6)
                add(bs * .5, t0 + (j + .5)*beat)
            mel = [notes[2]+12, notes[1]+12, notes[0]+12, notes[1]+12]
            for j in range(16):
                if j % 3 == 2: continue
                Ln = int(beat/4*SR); tn = np.arange(Ln)/SR
                p = lp(supersaw(mel[j % 4] + 12, Ln), .35) * np.exp(-tn*14)
                add(p * .22, t0 + j*beat/4, .35 if j % 2 else -.35)
        elif style in ("trap", "phonk"):
            Lk = int(bar*SR*.5); tk = np.arange(Lk)/SR
            b808 = np.tanh(2*np.sin(2*np.pi*np.cumsum(f(r-24)*(1+.8*np.exp(-tk*25)))/SR)) * np.exp(-tk*2.2)
            add(b808 * .7, t0); add(b808[:int(1.4*beat*SR)] * .6, t0 + 2.5*beat)
            add(clap() * .55, t0 + 2*beat)
            for j in range(16):
                if j in (6, 7, 14, 15):
                    for s in range(3): add(hat() * .16, t0 + (j + s/3)*beat/4, .25)
                else: add(hat() * .2, t0 + j*beat/4, .25)
            if style == "phonk":
                add(clap() * .5, t0); 
                cb = [0, 0, 3, 0, 7, 5, 3, 0]
                for j, iv in enumerate(cb):
                    Ln = int(beat/2*SR); tn = np.arange(Ln)/SR; fr = f(r+24+iv)
                    c = (np.sign(np.sin(2*np.pi*fr*tn)) + np.sign(np.sin(2*np.pi*fr*1.48*tn))) * np.exp(-tn*9)
                    add(lp(c, .3) * .13, t0 + j*beat/2, .2)
                t0 += bar; k += 1; continue
            bell = [notes[0]+24, notes[2]+24, notes[1]+24, notes[2]+24, notes[0]+36, notes[2]+24]
            for j, m in enumerate(bell):
                Ln = int(.5*SR); tn = np.arange(Ln)/SR
                b = (np.sin(2*np.pi*f(m)*tn) + .4*np.sin(2*np.pi*f(m)*2.76*tn)) * np.exp(-tn*7)
                add(b * .12, t0 + j*beat*2/3, -.3)
        else:  # pop / future bass
            for j in range(4):
                add(kick(dec=10) * .85, t0 + j*beat)
                if j % 2: add(clap() * .5, t0 + j*beat)
                for h in (.25, .5, .75): add(hat() * .12, t0 + (j+h)*beat, .3)
            chop = [0, .75, 1.5, 2, 2.75, 3.5]
            for c in chop:
                Ln = int(beat*.5*SR); tn = np.arange(Ln)/SR
                st = sum(supersaw(m+24, Ln) for m in notes)/3 * np.exp(-tn*5)
                add(lp(st, .4) * .3, t0 + c*beat, -.25 if c % 1 else .25)
            Lo = int(bar*SR); to = np.arange(Lo)/SR
            add(np.sin(2*np.pi*f(r-12)*to) * seg * .35, t0)
    t0 += bar; k += 1
# glue
for d, g in ((.023, .25), (.041, .2), (.067, .15)):
    D = int(d*SR); L2 = L_.copy(); L_[D:] += R_[:-D]*g*.4; R_[D:] += L2[:-D]*g*.4
mx = np.stack([L_, R_], 1)
fo = int(1.2*SR); mx[-fo:] *= np.linspace(1, 0, fo)[:, None]
mx = np.tanh(mx / np.abs(mx).max() * 1.8) * .9
w = wave.open(out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mx * 32767).astype(np.int16).tobytes()); w.close(); print(out)
