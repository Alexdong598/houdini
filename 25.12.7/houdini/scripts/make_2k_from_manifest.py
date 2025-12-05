# -- coding utf-8 --

Standalone read a manifest (one absolute path per line) and write 2K copies beside them.
- Default output src_dir2kstem_2kext
- Finds hoiiotool via HFSHB; else falls back to oiiotool in PATH.
- Skips existing outputs. Prints a summary.

Usage
  python make_2k_from_manifest.py --manifest pathtomanifest.txt [--res 2048x2048] [--filter lanczos3]


import os, sys, argparse, subprocess, shutil

def _normalize_native(p)
    alt = os.path.altsep
    if alt and alt in p
        p = p.replace(alt, os.sep)
    other =  if os.sep !=  else 
    if other in p
        p = p.replace(other, os.sep)
    return os.path.normpath(p)

def _find_oiio_tool()
    hfs = os.environ.get(HFS) or os.environ.get(HB)
    if hfs
        cand = os.path.join(_normalize_native(hfs), bin, hoiiotool.exe if os.name == nt else hoiiotool)
        if os.path.isfile(cand)
            return cand
    for name in (oiiotool.exe, oiiotool)
        which = shutil.which(name)
        if which
            return which
    raise RuntimeError(Cannot find hoiiotooloiiotool. Set HFSHB or put oiiotool on PATH.)

def _expected_2k_path(src_path, out_dir_name=2k, suffix=_2k)
    src_dir, src_name = os.path.split(src_path)
    stem, ext = os.path.splitext(src_name)
    out_dir = os.path.join(src_dir, out_dir_name)
    out_name = f{stem}{suffix}{ext}
    return os.path.join(out_dir, out_name)

def process_manifest(manifest_path, target_res=2048x2048, filter_name=lanczos3, alpha_safe=False)
    tool = _find_oiio_tool()
    processed, skipped = [], []

    with open(manifest_path, r, encoding=utf-8) as f
        paths = [line.strip() for line in f if line.strip()]

    # dedupe while preserving order
    seen, uniq = set(), []
    for p in paths
        np = _normalize_native(p)
        if np not in seen
            seen.add(np)
            uniq.append(np)

    for src in uniq
        if not os.path.isfile(src)
            skipped.append((src, missing on disk))
            continue

        dst = _expected_2k_path(src, out_dir_name=2k, suffix=_2k)
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        if os.path.isfile(dst)
            skipped.append((src, exists))
            continue

        cmd = [tool, src]
        if alpha_safe
            cmd.extend([--unpremult])
        cmd.extend([f--resizefilter={filter_name}, target_res])
        if alpha_safe
            cmd.extend([--premult])
        cmd.extend([-o, dst])

        try
            subprocess.run(cmd, check=True)
            processed.append(dst)
            print([2K-WRITE], dst)
        except subprocess.CalledProcessError as e
            skipped.append((src, foiiotool failed exit {e.returncode}))
        except Exception as e
            skipped.append((src, ferror {e}))

    # Summary
    print(n==== SUMMARY ====)
    print(Processed, len(processed))
    for p in processed
        print(  +, p)
    print(Skipped, len(skipped))
    for s, r in skipped
        print(  -, s, -, r)

def main()
    ap = argparse.ArgumentParser()
    ap.add_argument(--manifest, required=True, help=Path to manifest .txt (one absolute path per line).)
    ap.add_argument(--res, default=2048x2048, help='Target resolution token, e.g. 2048x2048 or 2048x.')
    ap.add_argument(--filter, default=lanczos3, help=Downsample filter for oiiotool (e.g. lanczos3, box, triangle).)
    ap.add_argument(--alpha-safe, action=store_true, help=Use unpremultpremult around resize.)
    args = ap.parse_args()

    manifest = _normalize_native(args.manifest)
    if not os.path.isfile(manifest)
        print(Manifest not found, manifest, file=sys.stderr)
        sys.exit(2)

    process_manifest(manifest, target_res=args.res, filter_name=args.filter, alpha_safe=args.alpha_safe)

if __name__ == __main__
    main()
