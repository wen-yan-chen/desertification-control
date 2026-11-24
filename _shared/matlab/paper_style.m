function S = paper_style(varargin)
%PAPER_STYLE Shared look for every data figure in the paper.
%   S = paper_style('out', dir, 'root', dir, 'palette', name)
%     out   where save_fig writes (default: the MCM_FIG_OUT environment
%           variable if set, else ./figures)
%     root  project folder holding Results/ and Data/ (default: the highest
%           folder above this kit that contains Results/v7, else the
%           current folder). Only the paper_figures scripts read S.res*.
%     palette  'oasis' (default, the final paper) or any name listed by
%              kit_palette(); the role colours below are re-mapped to it
%   Palette: mycolor.space, base colour #1E5F74 (deep oasis teal).
%     Twisted Spot palette : #1E5F74 #F49431 #FFEACE #8F7159
%     Generic Gradient     : #1E5F74 #00828C #01A494 #58C58C #A4E27C #F9F871
%     Squash / Skip grad.  : #2B633C (dark green), #4AC087 (mid green)
%     Grey Friends         : #344A53 #97AFB9
%   Axes follow the MATLAB template of the Zhihu column 阿昆的科研日常:
%   outward ticks on the left and bottom only, a thin closed frame, no minor
%   ticks, Times text, figure drawn at its printed size in centimetres.
%
%   Colour carries meaning in every figure:
%     water (store M, irrigation, W)   teal      #1E5F74
%     vegetation (cover V)             green     #2B633C / #4AC087
%     sand and wind (S, E)             brown     #8F7159, cream #FFEACE
%     model departure / highlight      orange    #F49431
%     limits and caps                  red dashed #D03B3B (project rule)

p = inputParser;
out = getenv('MCM_FIG_OUT');
if isempty(out), out = fullfile(pwd, 'figures'); end
addParameter(p, 'out', out);
addParameter(p, 'root', '');
addParameter(p, 'palette', 'oasis');
parse(p, varargin{:});
S.kit  = fileparts(fileparts(mfilename('fullpath')));
S.root = p.Results.root;
if isempty(S.root)
    S.root = pwd; d = S.kit;
    while true
        if isfolder(fullfile(d, 'Results', 'v7')), S.root = d; end
        up = fileparts(d);
        if strcmp(up, d), break; end
        d = up;
    end
end
S.out  = p.Results.out;
S.res  = fullfile(S.root, 'Results', 'v7', 'model1');
S.res2 = fullfile(S.root, 'Results', 'v7', 'model2');
S.res3 = fullfile(S.root, 'Results', 'v7', 'model3');
S.data = fullfile(S.root, 'Data', 'v7');

S.font  = 'Times New Roman';   % embeds in the PDF; matches the TeX Gyre Termes body text
S.textW = 16.5;                % \textwidth of the paper (469.76 pt), cm
S.halfW = 8.1;                 % 0.49\linewidth subfigure, cm

% font sizes (pt) for figures printed at their drawn size
S.fs.tick  = 7.5;
S.fs.label = 8;
S.fs.title = 8;
S.fs.note  = 7;

h = @hex2rgb;
c.water      = h('1E5F74');
c.waterMid   = h('659FB6');
c.waterLight = h('DCEBF1');
c.teal       = h('00828C');
c.veg        = h('2B633C');
c.vegMid     = h('4AC087');
c.vegLight   = h('E3F3E8');
c.sand       = h('8F7159');
c.sandLight  = h('FFEACE');
c.accent     = h('F49431');
c.pvDark     = h('D47216');
c.plum       = h('7A437F');
c.limit      = h('D03B3B');
c.ink        = h('1F2B33');
c.axis       = h('344A53');
c.grey       = h('97AFB9');
c.greyDark   = h('647B84');
c.grid       = h('E6EBED');
% irrigation levels, light to dark along the mycolor.space generic gradient
c.ramp = [h('97AFB9');   %    0 mm/yr (no irrigation, neutral)
          h('8CC66A');   %  100 (gradient lime #A4E27C, darkened for contrast on white)
          h('58C58C');   %  300
          h('01A494');   %  600
          h('00828C');   % 1000
          h('1E5F74')];  % 2000
S.palette = p.Results.palette;
S.cycle = [c.water; c.accent; c.veg; c.plum; c.sand; c.teal];   % series order for unnamed roles
if ~strcmp(S.palette, 'oasis')
    P = kit_palette(S.palette); k = P.cycle; S.cycle = k;
    mix = @(a, b, t) a * (1 - t) + b * t;
    c.water = k(1, :); c.waterMid = mix(k(1, :), 1, 0.38); c.waterLight = mix(k(1, :), 1, 0.84);
    c.accent = k(2, :); c.pvDark = mix(k(2, :), 0, 0.14); c.sandLight = mix(k(2, :), 1, 0.80);
    c.vegMid = k(3, :); c.veg = mix(k(3, :), 0, 0.28); c.vegLight = mix(k(3, :), 1, 0.84);
    c.plum = k(4, :); c.sand = k(5, :); c.teal = k(6, :);
    c.ramp = interp1([0 0.5 1], [c.grey; k(6, :); k(1, :)], linspace(0, 1, 6));
end
S.c = c;
end
