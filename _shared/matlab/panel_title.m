function t = panel_title(ax, str, S, overbar)
%PANEL_TITLE Left-aligned bold panel title.
%   overbar = true puts a bar over the final italic W (W-bar).
%   The title keeps MATLAB's automatic position so tiledlayout reserves room
%   for it; keep the top y tick below the upper limit so every title in a
%   layout sits at the same height.
if nargin < 4, overbar = false; end
ax.TitleHorizontalAlignment = 'left';
t = title(ax, str, 'FontName', S.font, 'FontSize', S.fs.title, ...
    'FontWeight', 'bold', 'Color', S.c.ink);
if overbar
    add_overbar(ax, t);
end
end
