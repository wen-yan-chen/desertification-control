function ridge_lines(ax, x, Y, labs, S, varargin)
%RIDGE_LINES Overlapping curves on stacked baselines; columns of Y are rows.
%   Use for a density or seasonal profile compared across many groups.
%   Options: overlap (curve height in row units, default 1.8), cmap (ramp name)
p = inputParser; addParameter(p, 'overlap', 1.8); addParameter(p, 'cmap', 'seq');
parse(p, varargin{:}); o = p.Results; c = S.c;
x = x(:); k = size(Y, 2); Y = o.overlap * Y / max(Y(:));
cm = kit_cmap(S, o.cmap, k + 3); cm = cm(3:end - 1, :);
style_axes(ax, S, 'x');
for j = 1:k                                              % back row first
    y0 = k - j;
    patch(ax, [x; flipud(x)], y0 + [Y(:, j); zeros(numel(x), 1)], cm(j, :), 'FaceAlpha', 0.88, 'EdgeColor', 'none');
    plot(ax, x, y0 + Y(:, j), '-', 'Color', 'w', 'LineWidth', 1.4);
    plot(ax, x, y0 + Y(:, j), '-', 'Color', 0.75 * cm(j, :), 'LineWidth', 0.6);
    plot(ax, x([1 end]), [y0 y0], '-', 'Color', c.grey, 'LineWidth', 0.4);
end
xlim(ax, [x(1) x(end)]); ylim(ax, [-0.15, k - 1 + o.overlap + 0.3]);
yticks(ax, 0:k - 1); yticklabels(ax, flip(string(labs))); ax.YAxis.TickLength = [0 0];
end
