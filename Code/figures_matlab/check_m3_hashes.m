function js = check_m3_hashes(S)
%CHECK_M3_HASHES Verify LF-normalised SHA-256 hashes in model3_results.json.
js = jsondecode(fileread(fullfile(S.res3, 'model3_results.json')));
fn = fieldnames(js.input_text_sha256_lf);
md = java.security.MessageDigest.getInstance('SHA-256');
for i = 1:numel(fn)
    rel = strrep(fn{i}, '_', '/'); % jsondecode turns path slashes/dots into valid identifiers; read raw map instead
end
% Parse raw key-value pairs directly so paths with slashes/dots are checked verbatim
raw = fileread(fullfile(S.res3, 'model3_results.json'));
tok = regexp(raw, '"([^"]+\.(?:json|csv|py))"\s*:\s*"([0-9a-f]{64})"', 'tokens');
assert(~isempty(tok), 'Could not parse input_text_sha256_lf from model3_results.json');
for k = 1:numel(tok)
    rel = tok{k}{1}; want = tok{k}{2};
    p = fullfile(S.root, rel);
    if ~isfile(p), continue; end
    fid = fopen(p, 'rb'); bytes = fread(fid, '*uint8'); fclose(fid);
    % CRLF -> LF normalisation
    cr = find(bytes(1:end-1) == 13 & bytes(2:end) == 10);
    if ~isempty(cr), bytes(cr) = []; end
    md.reset();
    dig = typecast(md.digest(bytes), 'uint8');
    got = lower(reshape(dec2hex(dig, 2).', 1, []));
    assert(strcmp(got, want), 'Hash mismatch for %s: got %s, expected %s', rel, got, want);
end
end
