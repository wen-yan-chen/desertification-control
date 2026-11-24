function save_fig(fig, name, S)
%SAVE_FIG Vector PDF for LaTeX plus a 400 dpi PNG preview, into S.out.
%   Set S.pdf = false to skip the PDF and S.dpi to change the PNG resolution.
drawnow;
if ~isfolder(S.out), mkdir(S.out); end
pdf = fullfile(S.out, [name '.pdf']);
png = fullfile(S.out, [name '.png']);
dpi = 400; if isfield(S, 'dpi'), dpi = S.dpi; end
if ~isfield(S, 'pdf') || S.pdf
    exportgraphics(fig, pdf, 'ContentType', 'vector', 'BackgroundColor', 'white');
end
exportgraphics(fig, png, 'Resolution', dpi, 'BackgroundColor', 'white');
fprintf('wrote %s\n', name);
close(fig);
end
