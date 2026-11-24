function raincloud_rows(ax, data, labs, S, varargin)
%RAINCLOUD_ROWS Distribution per group: density on top, quartile bar, raw points below.
%   data is a cell array of vectors. The thick bar spans the quartiles, the
%   thin line the 5th to 95th percentile, the white dot is the median.
%   Options: colors
p = inputParser; addParameter(p, 'colors', S.cycle);
parse(p, varargin{:}); o = p.Results;
n = numel(data); all = cell2mat(cellfun(@(v) v(:), data(:), 'UniformOutput', false));
lo = min(all); hi = max(all); pad = 0.06 * (hi - lo);
g = linspace(lo - pad, hi + pad, 160);
style_axes(ax, S, 'x');
for i = 1:n
    v = sort(data{i}(:)); m = numel(v); y0 = n - i + 1;
    col = o.colors(mod(i - 1, size(o.colors, 1)) + 1, :);
    bw = 1.06 * std(v) * m ^ (-1 / 5);
    dens = mean(exp(-0.5 * ((g - v) / bw) .^ 2), 1) / (bw * sqrt(2 * pi));
    dens = 0.4 * dens / max(dens);
    patch(ax, [g fliplr(g)], y0 + 0.07 + [dens zeros(size(g))], col, 'FaceAlpha', 0.5, ...
        'EdgeColor', col, 'LineWidth', 0.7);
    q = interp1(((1:m) - 0.5) / m, v, [0.05 0.25 0.5 0.75 0.95], 'linear', 'extrap');
    jit = mod((1:m)' * 0.6180339887, 1);                 % repeatable jitter
    plot(ax, v, y0 - 0.1 - 0.24 * jit, 'o', 'MarkerSize', 1.5, 'MarkerFaceColor', 0.55 * col + 0.45, ...
        'MarkerEdgeColor', 'none');
    plot(ax, q([1 5]), [y0 y0], '-', 'Color', col, 'LineWidth', 0.8);
    plot(ax, q([2 4]), [y0 y0], '-', 'Color', col, 'LineWidth', 3.2);
    plot(ax, q(3), y0, 'o', 'MarkerSize', 3.2, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', col, 'LineWidth', 0.8);
end
xlim(ax, [lo - pad, hi + pad]); ylim(ax, [0.55 n + 0.6]);
yticks(ax, 1:n); yticklabels(ax, flip(string(labs))); ax.YAxis.TickLength = [0 0];
end
