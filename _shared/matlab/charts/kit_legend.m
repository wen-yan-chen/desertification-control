function lg = kit_legend(ax, h, names, S, loc, ncol)
%KIT_LEGEND Small frameless legend in the paper font.
if nargin < 5, loc = 'best'; end
if nargin < 6, ncol = 1; end
lg = legend(ax, h, names, 'Location', loc, 'NumColumns', ncol, ...
    'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Box', 'off');
lg.ItemTokenSize = [10 5];
end
