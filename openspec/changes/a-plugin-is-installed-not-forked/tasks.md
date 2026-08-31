Every item is one failing test. Group 2 comes first because the source is what every
later group reads back, and the folder in group 3 is the second producer of it.

Ticked items are covered rather than counted: several items share one test where they
are one path — a contract version cora does not offer is refused *before* `extend` runs,
so 4.1 and 4.2 are the same assertion, and 4.3 is what every existing fixture proves by
declaring nothing. 5.5 falls out of the listing being driven by the plugins given, and
8.2 is a test of its own because a parametrisation that read no scopes would pass by
covering nothing.

## 1. The outer test

- [x] 1.1 **Outer.** Write a test that shows a plugin named as a module and a plugin
      dropped as a file both loaded, listed with their sources, scopes, tools and
      events, with a system-wide registration flagged. Mark it
      `@pytest.mark.xfail(strict=True)`

## 2. A plugin carries where it came from

- [x] 2.1 Write a test that shows a named module loaded with its module path as its source
- [x] 2.2 Write a test that shows a refusal quoting the source rather than a module path
- [x] 2.3 Write a test that shows two finders' extensions concatenated in the order the
      sources are read

## 3. A file in the folder is a plugin

- [x] 3.1 Write a test that shows a single `.py` file in the plugins folder loaded and
      registering
- [x] 3.2 Write a test that shows that file's stem heading its section of the brief
- [x] 3.3 Write a test that shows that file's settings read under its stem
- [x] 3.4 Write a test that shows the folder's files loaded in name order, after the
      named modules
- [x] 3.5 Write a test that shows a file that fails to import refused by its filename
- [x] 3.6 Write a test that shows a dropped file colliding with a named module refused,
      naming both
- [x] 3.7 Write a test that shows a missing plugins folder loading nothing and refusing
      nothing
- [x] 3.8 Write a test that shows a dropped file not shadowing an installed module of
      the same name
- [x] 3.9 Write a test that shows the plugins folder read from configuration, with a
      default

## 4. The contract has a version

- [x] 4.1 Write a test that shows a plugin declaring a version cora does not offer
      refused, naming both versions
- [x] 4.2 Write a test that shows such a plugin registering nothing before it is refused
- [x] 4.3 Write a test that shows a plugin declaring no version loaded
- [x] 4.4 Write a test that shows a version that is not a version refused by name

## 5. The listing

- [x] 5.1 Write a test that shows one plugin listed with its source, scopes, tools,
      instructions and events
- [x] 5.2 Write a test that shows a system-wide registration flagged and a scoped one not
- [x] 5.3 Write a test that shows a plugin registering under two scopes listed under both
- [x] 5.4 Write a test that shows a plugin that registered nothing listed with nothing
      under it
- [x] 5.5 Write a test that shows cora's own registrations kept out of the listing
- [x] 5.6 Write a test that shows a bare cora listed as loading nothing

## 6. The listing in a terminal

- [x] 6.1 Write a test that shows the rendering naming every plugin the listing holds
- [x] 6.2 Write a test that shows the rendering marking a system-wide registration
- [x] 6.3 Write a test that shows the rendering saying so when nothing is loaded

## 7. The listing on the screen

- [x] 7.1 Write a test that shows `/api/plugins` carrying the listing, plugin for plugin
- [x] 7.2 Write a test that shows the header menu drawing a plugin's scopes, tools and
      events
- [x] 7.3 Write a test that shows the menu marking a system-wide registration
- [x] 7.4 Write a test that shows the menu still saying "bare cora" when nothing loaded

## 8. Nothing cora ships names a plugin or a scope

- [x] 8.1 Write a guard that shows no shipped file naming a scope the shipped plugins
      register under
- [x] 8.2 Write a guard that shows the scope names read from the plugins rather than
      written into the guard
- [x] 8.3 Write a test that shows the travel plugin registering through the contract
      alone
- [x] 8.4 Bring the component-map guard green again over the assembly this change rewires

## 9. The marker comes off

- [x] 9.1 Drop 1.1's `xfail` marker and watch the outer test pass
