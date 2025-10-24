# improskop.github.io
Having completed this setup, the GitHub Page can be reached via:
https://arthurneudeck.github.io/improskop.github.io/
http://www.improskop.ch

## Setting Up GitHubPages
### Setup git
```git config --global http.postBuffer 157286400```

### [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
We publish on the "main" branch using the "docs" directory (as proposed as default).

### [Configuring a publishing source for your GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

### [Configuring a custom domain for your GitHub Pages site](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)
The following command should verify whether the DNS already resolves the domain properly:
```dig www.improskop.ch +noall +answer -t A```

The response should be:
```
; <<>> DiG 9.10.6 <<>> www.improskop.ch +noall +answer -t A
;; global options: +cmd
www.improskop.ch.       3600    IN      A       185.199.109.153
www.improskop.ch.       3600    IN      A       185.199.111.153
www.improskop.ch.       3600    IN      A       185.199.108.153
www.improskop.ch.       3600    IN      A       185.199.110.153
```