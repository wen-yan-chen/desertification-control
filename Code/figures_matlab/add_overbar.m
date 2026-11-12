function add_overbar(ax, t)
%ADD_OVERBAR Bar over the last letter of a horizontal text object (W -> W-bar).
%   MATLAB's TeX mode has no \overline. Works for titles and for text placed
%   in data units on linear axes; call it after the layout is final.
drawnow;
t.Units = 'data';
full = t.Extent;                                  % [x y w h], data units
probe = text(ax, 0, 0, '{\itW}', 'FontName', t.FontName, 'FontSize', t.FontSize, ...
    'FontWeight', t.FontWeight, 'Units', 'data', 'Visible', 'off');
w = probe.Extent(3);
delete(probe);
xr = full(1) + full(3) - 0.02 * w;                % right edge of the W
xl = xr - 0.80 * w;
y  = full(2) + 0.99 * full(4);
plot(ax, [xl xr], [y y], '-', 'Color', t.Color, 'LineWidth', 0.7, ...
    'Clipping', 'off', 'HandleVisibility', 'off');
end
