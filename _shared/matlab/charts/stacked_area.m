function h = stacked_area(ax, x, Y, S, varargin)
%STACKED_AREA Stacked areas over a shared x; columns of Y are the layers.
%   Options: names (written inside each layer where it is thickest),
%            colors, stream (true centres the stack on zero)
p = inputParser;
addParameter(p, 'names', {}); addParameter(p, 'colors', S.cycle); addParameter(p, 'stream', false);
parse(p, varargin{:}); o = p.Results;
x = x(:); k = size(Y, 2);
base = zeros(numel(x), 1); if o.stream, base = -sum(Y, 2) / 2; end
cumv = [base, base + cumsum(Y, 2)];
grid = 'y'; if o.stream, grid = 'none'; end
style_axes(ax, S, grid);
tot = max(cumv(:)) - min(cumv(:));
h = gobjects(1, k);
for j = 1:k
    h(j) = patch(ax, [x; flipud(x)], [cumv(:, j); flipud(cumv(:, j + 1))], o.colors(j, :), ...
        'EdgeColor', 'w', 'LineWidth', 0.5);
    th = max(Y(:, j)); near = find(Y(:, j) >= 0.97 * th);
    i = near(ceil(numel(near) / 2));                    % middle of the thickest stretch
    i = min(max(i, 3), numel(x) - 2);
    if ~isempty(o.names) && th > 0.07 * tot
        text(ax, x(i), mean(cumv(i, j:j + 1)), o.names{j}, 'FontName', S.font, 'FontSize', S.fs.note - 0.5, ...
            'Color', ink_on(o.colors(j, :), S), 'HorizontalAlignment', 'center');
    end
end
xlim(ax, [x(1) x(end)]); ylim(ax, [min(cumv(:)) max(cumv(:)) + 0.04 * tot]);
if o.stream, ax.YAxis.Visible = 'off'; end
end
