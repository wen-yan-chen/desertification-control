function S = paper_style()
%PAPER_STYLE Shared look for every data figure in the paper.
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

here = fileparts(mfilename('fullpath'));
S.root = fullfile(here, '..', '..');
S.out  = fullfile(S.root, 'Paper', 'Figure');
S.res  = fullfile(S.root, 'Results', 'v7', 'model1');
S.res2 = fullfile(S.root, 'Results', 'v7', 'model2');
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
S.c = c;
end
