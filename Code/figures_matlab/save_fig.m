function save_fig(fig, name, S)
%SAVE_FIG Vector PDF for LaTeX plus a 400 dpi PNG preview, into Paper/Figure.
drawnow;
pdf = fullfile(S.out, [name '.pdf']);
png = fullfile(S.out, [name '.png']);
exportgraphics(fig, pdf, 'ContentType', 'vector', 'BackgroundColor', 'white');
exportgraphics(fig, png, 'Resolution', 400, 'BackgroundColor', 'white');
fprintf('wrote %s\n', name);
close(fig);
end
